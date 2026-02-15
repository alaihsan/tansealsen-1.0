import os
import secrets
from datetime import datetime, timedelta
from flask import render_template, url_for, flash, redirect, request, abort, Blueprint, jsonify, current_app
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from werkzeug.utils import secure_filename
from functools import wraps
import time

from my_app.extensions import db
from my_app.models import User, Student, Violation, Classroom, School, ViolationRule, ViolationCategory, ViolationPhoto
from flask_login import login_user, current_user, logout_user, login_required

main = Blueprint('main', __name__)

# --- DECORATOR KHUSUS ---

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'super_admin':
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def school_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Super admin tidak boleh akses fitur input data pelanggaran langsung (harus login sbg school admin)
        if not current_user.is_authenticated or not current_user.school_id:
            flash("Anda harus login sebagai Admin Sekolah untuk mengakses halaman ini.", "warning")
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- SUPER ADMIN ROUTES ---

@main.route("/super-admin")
@super_admin_required
def super_dashboard():
    schools = School.query.all()
    total_users = User.query.count()
    return render_template('super_admin/dashboard.html', schools=schools, total_users=total_users)

@main.route("/super-admin/create-school", methods=['GET', 'POST'])
@super_admin_required
def create_school():
    if request.method == 'POST':
        school_name = request.form.get('school_name')
        address = request.form.get('address')
        admin_username = request.form.get('admin_username')
        admin_password = request.form.get('admin_password')
        
        # Validasi sederhana
        if School.query.filter_by(name=school_name).first():
            flash('Nama sekolah sudah terdaftar.', 'danger')
            return redirect(url_for('main.create_school'))
            
        if User.query.filter_by(username=admin_username).first():
            flash('Username admin sudah digunakan.', 'danger')
            return redirect(url_for('main.create_school'))

        # Buat Sekolah
        new_school = School(name=school_name, address=address)
        db.session.add(new_school)
        db.session.flush() # Generate ID
        
        # Buat User Admin Sekolah
        new_user = User(username=admin_username, role='school_admin', school_id=new_school.id, full_name="Administrator")
        new_user.set_password(admin_password)
        db.session.add(new_user)
        
        # Seed Default Data (Agar sekolah baru tidak kosong melompong)
        default_categories = [
            ('Ringan', 5), ('Sedang', 15), ('Berat', 30)
        ]
        for c_name, c_point in default_categories:
            db.session.add(ViolationCategory(name=c_name, points=c_point, school_id=new_school.id))
            
        default_rules = [
            ('Pasal 1', 'Ketertiban Umum'),
            ('Pasal 2', 'Kerapihan Seragam')
        ]
        for r_code, r_desc in default_rules:
            db.session.add(ViolationRule(code=r_code, description=r_desc, school_id=new_school.id))
        
        db.session.commit()
        flash(f'Sekolah "{school_name}" berhasil dibuat!', 'success')
        return redirect(url_for('main.super_dashboard'))
        
    return render_template('super_admin/create_school.html')

# --- PUBLIC / AUTH ROUTES ---

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'super_admin':
            return redirect(url_for('main.super_dashboard'))
        return redirect(url_for('main.home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):          
            login_user(user)
            
            # Redirect sesuai role
            if user.role == 'super_admin':
                return redirect(url_for('main.super_dashboard'))
            else:
                return redirect(url_for('main.home'))
        else:
            flash('Login Gagal. Cek username dan password', 'danger')
            
    return render_template('login.html')

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# --- SCHOOL ADMIN ROUTES (ISOLATED DATA) ---

@main.route("/")
@main.route("/home")
@main.route("/index")
@school_admin_required
def home():
    # Setup Filter
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    date_range = request.args.get('date_range', '')
    
    # FILTER UTAMA: Hanya ambil data dari sekolah user yang login
    # Join: Violation -> Student -> Check School ID
    query = Violation.query.join(Student).filter(Student.school_id == current_user.school_id)
    
    # Apply search filter
    if search:
        query = query.filter(Student.name.contains(search))
    
    # Apply category filter
    if category:
        query = query.filter(Violation.kategori_pelanggaran == category)
    
    # Apply date filter
    if date_range:
        today = datetime.utcnow()
        if date_range == 'today':
            query = query.filter(Violation.date_posted >= today.replace(hour=0, minute=0, second=0))
        elif date_range == 'week':
            query = query.filter(Violation.date_posted >= today - timedelta(days=7))
        elif date_range == 'month':
            query = query.filter(Violation.date_posted >= today - timedelta(days=30))
    
    # Eager load photos untuk efisiensi
    pelanggaran_pagination = query.options(joinedload(Violation.photos)).order_by(Violation.date_posted.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    # Dashboard Stats (Isolated)
    total_students = Student.query.filter_by(school_id=current_user.school_id).count()
    # Untuk violation count, kita butuh join
    total_violations = Violation.query.join(Student).filter(Student.school_id == current_user.school_id).count()
    total_classes = Classroom.query.filter_by(school_id=current_user.school_id).count()
    
    # Kirim daftar kategori untuk filter dropdown di dashboard
    categories = ViolationCategory.query.filter_by(school_id=current_user.school_id).all()
    
    return render_template('index.html', 
                           total_students=total_students, 
                           total_violations=total_violations,
                           total_classes=total_classes,
                           pelanggaran_pagination=pelanggaran_pagination,
                           search_query=search,
                           category_filter=category,
                           date_range_value=date_range,
                           categories=categories)

@main.route("/classes", methods=['GET', 'POST'])
@school_admin_required
def manage_classes():
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        if class_name:
            # Cek apakah kelas sudah ada DI SEKOLAH INI
            existing_class = Classroom.query.filter_by(name=class_name, school_id=current_user.school_id).first()
            if not existing_class:
                # Assign ke sekolah yang sedang login
                new_class = Classroom(name=class_name, school_id=current_user.school_id)
                db.session.add(new_class)
                db.session.commit()
                flash(f'Kelas {class_name} berhasil dibuat!', 'success')
            else:
                flash(f'Kelas {class_name} sudah ada di sekolah ini.', 'warning')
        return redirect(url_for('main.manage_classes'))
    
    # Tampilkan hanya kelas milik sekolah ini
    classes = Classroom.query.filter_by(school_id=current_user.school_id).order_by(Classroom.name).all()
    return render_template('manajemenkelas.html', classes=classes)

@main.route("/classes/delete/<int:class_id>", methods=['POST'])
@school_admin_required
def delete_class(class_id):
    # Pastikan kelas milik sekolah user (Security check)
    classroom = Classroom.query.filter_by(id=class_id, school_id=current_user.school_id).first_or_404()
    
    if classroom.students:
        flash('Tidak bisa menghapus kelas yang masih memiliki murid.', 'danger')
    else:
        db.session.delete(classroom)
        db.session.commit()
        flash('Kelas berhasil dihapus.', 'success')
    return redirect(url_for('main.manage_classes'))

@main.route("/classes/<int:class_id>", methods=['GET', 'POST'])
@school_admin_required
def view_class(class_id):
    # Security check: Ensure class belongs to current school
    classroom = Classroom.query.filter_by(id=class_id, school_id=current_user.school_id).first_or_404()
    
    # Get other classes for mutation (only from same school)
    all_classes = Classroom.query.filter(
        Classroom.id != class_id, 
        Classroom.school_id == current_user.school_id
    ).order_by(Classroom.name).all()

    # Logic Import/Tambah Murid
    if request.method == 'POST' and 'import_students' in request.form:
        raw_names = request.form.get('student_names')
        if raw_names:
            names_list = raw_names.strip().split('\n')
            count = 0
            for name in names_list:
                clean_name = name.strip()
                if clean_name:
                    dummy_nis = secrets.token_hex(4) 
                    # Assign Student ke Sekolah & Kelas
                    student = Student(
                        name=clean_name, 
                        nis=dummy_nis, 
                        classroom=classroom, 
                        school_id=current_user.school_id 
                    )
                    db.session.add(student)
                    count += 1
            db.session.commit()
            flash(f'Berhasil mengimpor {count} murid.', 'success')
            return redirect(url_for('main.view_class', class_id=class_id))

    # Logic Mutasi
    if request.method == 'POST' and 'mutate_students' in request.form:
        target_class_id = request.form.get('target_class_id')
        selected_student_ids = request.form.getlist('selected_students')
        
        if target_class_id and selected_student_ids:
            # Validasi kelas tujuan milik sekolah yang sama
            target_class = Classroom.query.filter_by(id=target_class_id, school_id=current_user.school_id).first()
            if target_class:
                for stud_id in selected_student_ids:
                    # Validasi siswa milik sekolah yang sama
                    student = Student.query.filter_by(id=stud_id, school_id=current_user.school_id).first()
                    if student:
                        student.classroom = target_class
                db.session.commit()
                flash('Mutasi berhasil.', 'success')
            else:
                flash('Kelas tujuan tidak valid.', 'danger')
        
        return redirect(url_for('main.view_class', class_id=class_id))

    return render_template('detailkelas.html', classroom=classroom, all_classes=all_classes)

@main.route("/api/students/<class_name>")
@school_admin_required
def get_students_by_class(class_name):
    # Filter kelas berdasarkan nama DAN sekolah
    classroom = Classroom.query.filter_by(name=class_name, school_id=current_user.school_id).first()
    if classroom:
        students = [student.name for student in classroom.students]
        students.sort()
        return jsonify(students)
    else:
        return jsonify([])

@main.route("/add_violation", methods=['GET', 'POST'])
@school_admin_required
def add_violation():
    # Hanya ambil data sekolah ini
    classes = Classroom.query.filter_by(school_id=current_user.school_id).order_by(Classroom.name).all()
    rules = ViolationRule.query.filter_by(school_id=current_user.school_id).all()
    categories = ViolationCategory.query.filter_by(school_id=current_user.school_id).all()
    staff_members = User.query.filter_by(school_id=current_user.school_id).all()
    
    if request.method == 'POST':
        class_name = request.form.get('kelas')
        student_name = request.form.get('nama_murid')
        description = request.form.get('deskripsi')
        pasal = request.form.get('pasal')
        kategori_id = request.form.get('kategori_id')
        tanggal_str = request.form.get('tanggal_kejadian')
        jam_str = request.form.get('jam_kejadian') # Ambil input jam
        di_input_oleh = request.form.get('di_input_oleh')
        
        # Cari kategori untuk dapat poin
        selected_category = ViolationCategory.query.get(kategori_id)
        points = selected_category.points if selected_category else 0
        kategori_name = selected_category.name if selected_category else "Umum"
            
        # Cari Siswa dengan validasi Sekolah
        classroom = Classroom.query.filter_by(name=class_name, school_id=current_user.school_id).first()
        student = None
        if classroom:
            student = Student.query.filter_by(name=student_name, classroom_id=classroom.id, school_id=current_user.school_id).first()
        
        if student:
            try:
                # GABUNGKAN TANGGAL DAN JAM
                date_obj = datetime.strptime(tanggal_str, '%d/%m/%Y')
                if jam_str:
                    time_obj = datetime.strptime(jam_str, '%H:%M').time()
                    date_posted = datetime.combine(date_obj.date(), time_obj)
                else:
                    date_posted = date_obj # Fallback jika jam kosong (walaupun required)
            except (ValueError, TypeError):
                date_posted = datetime.utcnow()

            # 1. Buat Object Pelanggaran
            violation = Violation(
                description=description,
                points=points,
                date_posted=date_posted,
                student_id=student.id,
                pasal=pasal,
                kategori_pelanggaran=kategori_name,
                di_input_oleh=di_input_oleh
            )
            db.session.add(violation)
            db.session.flush() # Ambil ID violation sebelum commit

            # 2. Handle Multiple Files (Maks 10)
            files = request.files.getlist('bukti_file')
            
            # Filter hanya file yang ada namanya
            valid_files = [f for f in files if f.filename != '']
            
            # Ambil maksimal 10
            for file in valid_files[:10]: 
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)  
                fname = secure_filename(file.filename)
                import time
                timestamp = str(int(time.time()))
                # Tambahkan random string kecil untuk menghindari tabrakan nama di detik yang sama
                unique_suffix = secrets.token_hex(2)
                filename = f"{timestamp}_{unique_suffix}_{fname}"
                
                file.save(os.path.join(upload_folder, filename))
                
                # Simpan ke tabel foto
                photo = ViolationPhoto(filename=filename, violation_id=violation.id)
                db.session.add(photo)

            db.session.commit()
            flash('Pelanggaran berhasil dicatat dengan waktu yang spesifik!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash(f'Siswa tidak ditemukan di database sekolah ini.', 'danger')

    return render_template('add_violation.html', classes=classes, rules=rules, categories=categories, staff_members=staff_members)

@main.route("/student/<int:student_id>")
@school_admin_required
def student_history(student_id):
    # Validasi siswa milik sekolah user
    student = Student.query.filter_by(id=student_id, school_id=current_user.school_id).first_or_404()
    total_points = sum(v.points for v in student.violations)
    return render_template('student_history.html', student=student, total_points=total_points)

@main.route("/statistics")
@school_admin_required
def statistics():
    # Filter Violation join Student filter by School ID
    base_query = Violation.query.join(Student).filter(Student.school_id == current_user.school_id)
    
    # 1. Pie Chart Data (Dinamis berdasarkan kategori DB)
    category_stats = db.session.query(
        Violation.kategori_pelanggaran, func.count(Violation.id)
    ).join(Student).filter(Student.school_id == current_user.school_id).group_by(Violation.kategori_pelanggaran).all()
    
    pie_labels = [stat[0] for stat in category_stats]
    pie_data = [stat[1] for stat in category_stats]
    
    if not pie_data:
        pie_labels = ["Belum ada data"]
        pie_data = [0]
    
    # 2. Top 5 Hari Ini (Filtered by School)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    tomorrow = today + timedelta(days=1)
    
    top_today = db.session.query(
        Student,
        func.count(Violation.id).label('count'),
        func.sum(Violation.points).label('total_points')
    ).join(Violation).filter(
        Student.school_id == current_user.school_id, # Filter Sekolah
        Violation.date_posted >= today,
        Violation.date_posted < tomorrow
    ).group_by(Student.id).order_by(func.sum(Violation.points).desc()).limit(5).all()
    
    # 3. Trend Line (Filtered by School)
    trend_range = request.args.get('trend_range', '7d')
    end_date = datetime.utcnow()
    days_map = {'30d': 30, '90d': 90, '180d': 180}
    start_date = end_date - timedelta(days=days_map.get(trend_range, 7))
    
    daily_stats = db.session.query(
        func.date(Violation.date_posted).label('date'),
        func.count(Violation.id).label('count')
    ).join(Student).filter(
        Student.school_id == current_user.school_id, # Filter Sekolah
        Violation.date_posted >= start_date
    ).group_by(
        func.date(Violation.date_posted)
    ).all()
    
    stats_dict = {str(stat.date): stat.count for stat in daily_stats}
    trend_labels = []
    trend_data = []
    
    current = start_date
    while current <= end_date:
        d_str = current.strftime('%Y-%m-%d')
        l_str = current.strftime('%d %b')
        trend_labels.append(l_str)
        trend_data.append(stats_dict.get(d_str, 0))
        current += timedelta(days=1)

    return render_template(
        'statistics.html',
        pie_data=pie_data,
        pie_labels=pie_labels,
        top_today=top_today,
        trend_labels=trend_labels,
        trend_data=trend_data,
        current_range=trend_range,
        total_violations_today=sum(item.count for item in top_today) if top_today else 0
    )

# --- MENU PENGATURAN (SETTINGS) ---

@main.route("/settings")
@school_admin_required
def settings():
    # Ambil data untuk semua tab
    school = current_user.school
    members = User.query.filter_by(school_id=school.id).all()
    rules = ViolationRule.query.filter_by(school_id=school.id).all()
    categories = ViolationCategory.query.filter_by(school_id=school.id).all()
    
    return render_template('settings.html', school=school, members=members, rules=rules, categories=categories)

@main.route("/settings/update_school", methods=['POST'])
@school_admin_required
def settings_update_school():
    name = request.form.get('name')
    address = request.form.get('address')
    
    school = current_user.school
    if name: school.name = name
    if address: school.address = address
    
    # Handle Logo Upload
    if 'logo' in request.files:
        file = request.files['logo']
        if file and file.filename:
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_folder): os.makedirs(upload_folder)
            
            fname = secure_filename(file.filename)
            import time
            timestamp = str(int(time.time()))
            filename = f"logo_{school.id}_{timestamp}_{fname}"
            file.save(os.path.join(upload_folder, filename))
            school.logo = filename

    db.session.commit()
    flash('Profil sekolah berhasil diperbarui.', 'success')
    return redirect(url_for('main.settings'))

@main.route("/settings/add_member", methods=['POST'])
@school_admin_required
def settings_add_member():
    username = request.form.get('username')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    
    if User.query.filter_by(username=username).first():
        flash('Username sudah digunakan.', 'danger')
        return redirect(url_for('main.settings'))
        
    new_user = User(username=username, full_name=full_name, role='school_admin', school_id=current_user.school_id)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash('Anggota baru berhasil ditambahkan.', 'success')
    return redirect(url_for('main.settings'))

@main.route("/settings/edit_member", methods=['POST'])
@school_admin_required
def settings_edit_member():
    user_id = request.form.get('user_id')
    password = request.form.get('password')
    username = request.form.get('username') # Jika ingin ganti username
    
    user = User.query.filter_by(id=user_id, school_id=current_user.school_id).first()
    if user:
        if username and username != user.username:
            if User.query.filter_by(username=username).first():
                flash('Username sudah terpakai.', 'danger')
                return redirect(url_for('main.settings'))
            user.username = username
            
        if password:
            user.set_password(password)
            flash(f'Password untuk {user.username} berhasil direset.', 'success')
        else:
            flash('Data anggota diperbarui.', 'success')
        db.session.commit()
    else:
        flash('User tidak ditemukan.', 'danger')
        
    return redirect(url_for('main.settings'))

@main.route("/settings/delete_member/<int:user_id>", methods=['POST'])
@school_admin_required
def settings_delete_member(user_id):
    if user_id == current_user.id:
        flash('Anda tidak bisa menghapus akun sendiri.', 'warning')
        return redirect(url_for('main.settings'))
        
    user = User.query.filter_by(id=user_id, school_id=current_user.school_id).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('Anggota berhasil dihapus.', 'success')
    return redirect(url_for('main.settings'))

@main.route("/settings/rules", methods=['POST'])
@school_admin_required
def settings_rules():
    action = request.form.get('action')
    if action == 'add':
        code = request.form.get('code')
        desc = request.form.get('description')
        rule = ViolationRule(code=code, description=desc, school_id=current_user.school_id)
        db.session.add(rule)
        
    elif action == 'delete':
        rule_id = request.form.get('rule_id')
        rule = ViolationRule.query.filter_by(id=rule_id, school_id=current_user.school_id).first()
        if rule: db.session.delete(rule)
        
    db.session.commit()
    return redirect(url_for('main.settings'))

@main.route("/settings/categories", methods=['POST'])
@school_admin_required
def settings_categories():
    action = request.form.get('action')
    if action == 'add':
        name = request.form.get('name')
        points = request.form.get('points')
        cat = ViolationCategory(name=name, points=points, school_id=current_user.school_id)
        db.session.add(cat)
        
    elif action == 'delete':
        cat_id = request.form.get('cat_id')
        cat = ViolationCategory.query.filter_by(id=cat_id, school_id=current_user.school_id).first()
        if cat: db.session.delete(cat)
        
    db.session.commit()
    return redirect(url_for('main.settings'))