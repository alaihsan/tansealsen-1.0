import os
import secrets
from datetime import datetime, timedelta
from flask import render_template, url_for, flash, redirect, request, abort, Blueprint, jsonify, current_app
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from werkzeug.utils import secure_filename
from functools import wraps

from my_app.extensions import db
from my_app.models import User, Student, Violation, Classroom, School
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
        new_user = User(username=admin_username, role='school_admin', school_id=new_school.id)
        new_user.set_password(admin_password)
        db.session.add(new_user)
        
        db.session.commit()
        flash(f'Sekolah "{school_name}" dan Admin "{admin_username}" berhasil dibuat!', 'success')
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
        if category == 'Ringan':
            query = query.filter(Violation.points <= 10)
        elif category == 'Sedang':
            query = query.filter(Violation.points.between(11, 20))
        elif category == 'Berat':
            query = query.filter(Violation.points > 20)
    
    # Apply date filter
    if date_range:
        today = datetime.utcnow()
        if date_range == 'today':
            query = query.filter(Violation.date_posted >= today.replace(hour=0, minute=0, second=0))
        elif date_range == 'week':
            query = query.filter(Violation.date_posted >= today - timedelta(days=7))
        elif date_range == 'month':
            query = query.filter(Violation.date_posted >= today - timedelta(days=30))
    
    pelanggaran_pagination = query.order_by(Violation.date_posted.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    # Dashboard Stats (Isolated)
    total_students = Student.query.filter_by(school_id=current_user.school_id).count()
    # Untuk violation count, kita butuh join
    total_violations = Violation.query.join(Student).filter(Student.school_id == current_user.school_id).count()
    total_classes = Classroom.query.filter_by(school_id=current_user.school_id).count()
    
    return render_template('index.html', 
                           total_students=total_students, 
                           total_violations=total_violations,
                           total_classes=total_classes,
                           pelanggaran_pagination=pelanggaran_pagination,
                           search_query=search,
                           category_filter=category,
                           date_range_value=date_range)

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
    # Hanya ambil kelas sekolah ini
    classes = Classroom.query.filter_by(school_id=current_user.school_id).order_by(Classroom.name).all()
    
    if request.method == 'POST':
        # Logic simpan sama, tapi pastikan validasi sekolah
        class_name = request.form.get('kelas')
        student_name = request.form.get('nama_murid')
        description = request.form.get('deskripsi')
        # ... (ambil field lain seperti biasa) ...
        pasal = request.form.get('pasal')
        kategori = request.form.get('kategori_pelanggaran')
        tanggal_str = request.form.get('tanggal_kejadian')
        di_input_oleh = request.form.get('di_input_oleh')
        
        # Calculate points
        points = 0
        if kategori == 'Ringan': points = 5
        elif kategori == 'Sedang': points = 15
        elif kategori == 'Berat': points = 30
            
        # Cari Siswa dengan validasi Sekolah
        classroom = Classroom.query.filter_by(name=class_name, school_id=current_user.school_id).first()
        student = None
        if classroom:
            student = Student.query.filter_by(name=student_name, classroom_id=classroom.id, school_id=current_user.school_id).first()
        
        if student:
            # Handle Upload File ... (Logic upload file sama seperti sebelumnya)
            filename = None
            if 'bukti_file' in request.files:
                file = request.files['bukti_file']
                if file and file.filename:
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)  
                    fname = secure_filename(file.filename)
                    import time
                    timestamp = str(int(time.time()))
                    filename = f"{timestamp}_{fname}"
                    file.save(os.path.join(upload_folder, filename))

            try:
                date_posted = datetime.strptime(tanggal_str, '%d/%m/%Y')
            except (ValueError, TypeError):
                date_posted = datetime.utcnow()

            violation = Violation(
                description=description,
                points=points,
                date_posted=date_posted,
                student_id=student.id,
                pasal=pasal,
                kategori_pelanggaran=kategori,
                di_input_oleh=di_input_oleh,
                bukti_file=filename
            )
            db.session.add(violation)
            db.session.commit()
            flash('Pelanggaran berhasil dicatat!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash(f'Siswa tidak ditemukan di database sekolah ini.', 'danger')

    return render_template('add_violation.html', form_data={}, classes=classes)

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
    
    # 1. Pie Chart Data
    cat_ringan = base_query.filter(Violation.kategori_pelanggaran == 'Ringan').count()
    cat_sedang = base_query.filter(Violation.kategori_pelanggaran == 'Sedang').count()
    cat_berat = base_query.filter(Violation.kategori_pelanggaran == 'Berat').count()
    pie_data = [cat_ringan, cat_sedang, cat_berat]
    
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
        top_today=top_today,
        trend_labels=trend_labels,
        trend_data=trend_data,
        current_range=trend_range,
        total_violations_today=sum(item.count for item in top_today) if top_today else 0
    )