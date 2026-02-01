import os
import secrets
from datetime import datetime
from flask import render_template, url_for, flash, redirect, request, abort, Blueprint, jsonify, current_app
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from my_app.extensions import db, bcrypt
from my_app.models import User, Student, Violation, Classroom
from flask_login import login_user, current_user, logout_user, login_required

main = Blueprint('main', __name__)

# --- Halaman Utama ---
@main.route("/")
@main.route("/home")
@main.route("/index")
@login_required
def home():
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    date_range = request.args.get('date_range', '')
    
    # Build query - ensure student relationship is loaded and filter out violations without students
    query = Violation.query.options(joinedload(Violation.student)).join(Violation.student)
    
    # Apply search filter
    if search:
        query = query.join(Student).filter(Student.name.contains(search))
    
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
        from datetime import timedelta
        today = datetime.utcnow()
        if date_range == 'today':
            query = query.filter(Violation.date_posted >= today.replace(hour=0, minute=0, second=0))
        elif date_range == 'week':
            query = query.filter(Violation.date_posted >= today - timedelta(days=7))
        elif date_range == 'month':
            query = query.filter(Violation.date_posted >= today - timedelta(days=30))
    
    # Get pagination
    pelanggaran_pagination = query.order_by(Violation.date_posted.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # Dashboard stats
    total_students = Student.query.count()
    total_violations = Violation.query.count()
    total_classes = Classroom.query.count()
    recent_violations = Violation.query.order_by(Violation.date_posted.desc()).limit(5).all()
    
    return render_template('index.html', 
                           total_students=total_students, 
                           total_violations=total_violations,
                           total_classes=total_classes,
                           recent_violations=recent_violations,
                           pelanggaran_pagination=pelanggaran_pagination,
                           search_query=search,
                           category_filter=category,
                           date_range_value=date_range)

# --- MANAJEMEN KELAS ---

@main.route("/classes", methods=['GET', 'POST'])
@login_required
def manage_classes():
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        if class_name:
            existing_class = Classroom.query.filter_by(name=class_name).first()
            if not existing_class:
                new_class = Classroom(name=class_name)
                db.session.add(new_class)
                db.session.commit()
                flash(f'Kelas {class_name} berhasil dibuat!', 'success')
            else:
                flash(f'Kelas {class_name} sudah ada.', 'warning')
        return redirect(url_for('main.manage_classes'))
    
    classes = Classroom.query.order_by(Classroom.name).all()
    return render_template('manajemenkelas.html', classes=classes)

@main.route("/classes/delete/<int:class_id>", methods=['POST'])
@login_required
def delete_class(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.students:
        flash('Tidak bisa menghapus kelas yang masih memiliki murid. Pindahkan atau hapus murid terlebih dahulu.', 'danger')
    else:
        db.session.delete(classroom)
        db.session.commit()
        flash('Kelas berhasil dihapus.', 'success')
    return redirect(url_for('main.manage_classes'))

@main.route("/classes/<int:class_id>", methods=['GET', 'POST'])
@login_required
def view_class(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    all_classes = Classroom.query.filter(Classroom.id != class_id).order_by(Classroom.name).all()

    # Logic Import/Tambah Murid Cepat
    if request.method == 'POST' and 'import_students' in request.form:
        raw_names = request.form.get('student_names')
        if raw_names:
            names_list = raw_names.strip().split('\n')
            count = 0
            for name in names_list:
                clean_name = name.strip()
                if clean_name:
                    dummy_nis = secrets.token_hex(4) 
                    student = Student(name=clean_name, nis=dummy_nis, classroom=classroom)
                    db.session.add(student)
                    count += 1
            db.session.commit()
            flash(f'Berhasil mengimpor {count} murid ke kelas {classroom.name}.', 'success')
            return redirect(url_for('main.view_class', class_id=class_id))

    # Logic Mutasi (Pindah Kelas)
    if request.method == 'POST' and 'mutate_students' in request.form:
        target_class_id = request.form.get('target_class_id')
        selected_student_ids = request.form.getlist('selected_students')
        
        if target_class_id and selected_student_ids:
            target_class = Classroom.query.get(target_class_id)
            if target_class:
                for stud_id in selected_student_ids:
                    student = Student.query.get(stud_id)
                    if student:
                        student.classroom = target_class
                
                db.session.commit()
                flash(f'{len(selected_student_ids)} murid berhasil dipindahkan ke {target_class.name}.', 'success')
            else:
                flash('Kelas tujuan tidak valid.', 'danger')
        else:
            flash('Pilih kelas tujuan dan minimal satu murid.', 'warning')
        
        return redirect(url_for('main.view_class', class_id=class_id))

    return render_template('detailkelas.html', classroom=classroom, all_classes=all_classes)


# --- FITUR PELANGGARAN ---

# [FIX] API Endpoint untuk mengambil data siswa berdasarkan kelas (AJAX)
@main.route("/api/students/<class_name>")
@login_required
def get_students_by_class(class_name):
    classroom = Classroom.query.filter_by(name=class_name).first()
    if classroom:
        # Mengambil nama siswa dan mengurutkannya
        students = [student.name for student in classroom.students]
        students.sort()
        return jsonify(students)
    else:
        # Kelas tidak ditemukan atau kosong
        return jsonify([])

@main.route("/add_violation", methods=['GET', 'POST'])
@login_required
def add_violation():
    # Mengambil list kelas untuk validasi atau keperluan lain jika perlu
    classes = Classroom.query.order_by(Classroom.name).all()
    
    if request.method == 'POST':
        # Ambil data dari form HTML yang baru
        class_name = request.form.get('kelas')
        student_name = request.form.get('nama_murid')
        description = request.form.get('deskripsi')
        pasal = request.form.get('pasal')
        kategori = request.form.get('kategori_pelanggaran')
        tanggal_str = request.form.get('tanggal_kejadian')
        di_input_oleh = request.form.get('di_input_oleh')
        
        # Mapping Kategori ke Poin (Sesuai kesepakatan)
        points = 0
        if kategori == 'Ringan':
            points = 5
        elif kategori == 'Sedang':
            points = 15
        elif kategori == 'Berat':
            points = 30
            
        # Validasi dasar
        if not (class_name and student_name and description and kategori):
            flash('Mohon lengkapi data wajib (Kelas, Nama, Kategori, Deskripsi).', 'danger')
            return redirect(url_for('main.add_violation'))

        # Cari ID Siswa berdasarkan Nama dan Kelas
        classroom = Classroom.query.filter_by(name=class_name).first()
        student = None
        if classroom:
            student = Student.query.filter_by(name=student_name, classroom_id=classroom.id).first()
        
        if student:
            # Handle Upload Bukti (Opsional)
            filename = None
            if 'bukti_file' in request.files:
                file = request.files['bukti_file']
                if file and file.filename:
                    # Pastikan folder uploads ada
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                        
                    fname = secure_filename(file.filename)
                    # Tambahkan timestamp agar unik
                    import time
                    timestamp = str(int(time.time()))
                    filename = f"{timestamp}_{fname}"
                    file.save(os.path.join(upload_folder, filename))

            # Simpan Pelanggaran
            
            # Parsing tanggal kejadian
            try:
                date_posted = datetime.strptime(tanggal_str, '%d/%m/%Y')
            except (ValueError, TypeError):
                date_posted = datetime.utcnow()

            # Create object with all fields
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
            flash(f'Siswa "{student_name}" tidak ditemukan di kelas {class_name}.', 'danger')

    return render_template('add_violation.html', form_data={}, classes=classes)

@main.route("/student/<int:student_id>")
@login_required
def student_history(student_id):
    student = Student.query.get_or_404(student_id)
    total_points = sum(v.points for v in student.violations)
    return render_template('student_history.html', student=student, total_points=total_points)

# --- AUTHENTICATION ---

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):          
            login_user(user)
            return redirect(url_for('main.home'))
        else:
            flash('Login Gagal. Cek username dan password', 'danger')
    return render_template('login.html')

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route("/statistics")
@login_required
def statistics():
    custom_range = request.args.get('custom_range', '')
    
    total_violations = Violation.query.count()
    total_students = Student.query.count()
    
    # Filter stats
    ringan_violations = Violation.query.filter(Violation.points <= 10).count()
    sedang_violations = Violation.query.filter(Violation.points.between(11, 20)).count()
    berat_violations = Violation.query.filter(Violation.points > 20).count()
    
    # Today's stats
    from datetime import timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_violations = Violation.query.filter(Violation.date_posted >= today).all()
    today_ringan = len([v for v in today_violations if v.points <= 10])
    today_sedang = len([v for v in today_violations if 11 <= v.points <= 20])
    today_berat = len([v for v in today_violations if v.points > 20])
    
    # Top violators
    top_violators = db.session.query(
        Student.id.label('student_id'),
        Student.name,
        db.func.count(Violation.id).label('violation_count'),
        db.func.sum(Violation.points).label('total_points')
    ).join(Violation).group_by(Student.id, Student.name).order_by(db.func.sum(Violation.points).desc()).limit(10).all()
    
    stats_data = {
        'total_violations': total_violations,
        'total_students': total_students,
        'ringan_violations': ringan_violations,
        'sedang_violations': sedang_violations,
        'berat_violations': berat_violations,
        'today_ringan': today_ringan,
        'today_sedang': today_sedang,
        'today_berat': today_berat,
        'custom_range': custom_range
    }
    
    return render_template('statistics.html', stats_data=stats_data, top_violators=top_violators)