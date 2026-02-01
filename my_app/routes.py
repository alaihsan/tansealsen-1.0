import os
import secrets
from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from sqlalchemy.orm import joinedload
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
    from flask import request
    
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
        from datetime import datetime, timedelta
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

# --- MANAJEMEN KELAS (Baru) ---

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
    # Opsional: Cek apakah ada murid sebelum menghapus
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
    all_classes = Classroom.query.filter(Classroom.id != class_id).order_by(Classroom.name).all() # Untuk dropdown mutasi

    # Logic Import/Tambah Murid Cepat
    if request.method == 'POST' and 'import_students' in request.form:
        raw_names = request.form.get('student_names')
        if raw_names:
            names_list = raw_names.strip().split('\n')
            count = 0
            for name in names_list:
                clean_name = name.strip()
                if clean_name:
                    # Generate NIS dummy atau ambil dari input jika ada format khusus
                    # Di sini kita pakai timestamp/random sederhana untuk NIS unik
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
                        student.classroom = target_class # Update kelas (Mutasi)
                        # Catatan: History violation TETAP tersimpan di student.violations
                
                db.session.commit()
                flash(f'{len(selected_student_ids)} murid berhasil dipindahkan ke {target_class.name}.', 'success')
            else:
                flash('Kelas tujuan tidak valid.', 'danger')
        else:
            flash('Pilih kelas tujuan dan minimal satu murid.', 'warning')
        
        return redirect(url_for('main.view_class', class_id=class_id))

    return render_template('detailkelas.html', classroom=classroom, all_classes=all_classes)


# --- FITUR PELANGGARAN (Existing, Adjusted) ---

@main.route("/add_violation", methods=['GET', 'POST'])
@login_required
def add_violation():
    # Mengambil semua siswa untuk dropdown pencarian
    students = Student.query.all()
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        description = request.form.get('description')
        points = request.form.get('points')

        if student_id and description and points:
            violation = Violation(description=description, points=int(points), student_id=student_id)
            db.session.add(violation)
            db.session.commit()
            flash('Pelanggaran berhasil dicatat!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Mohon lengkapi semua form.', 'danger')
            
    return render_template('add_violation.html', students=students, form_data={})

@main.route("/student/<int:student_id>")
@login_required
def student_history(student_id):
    student = Student.query.get_or_404(student_id)
    # Menghitung total poin
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
        if user and bcrypt.check_password_hash(user.password, password):
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
    # Get query parameters
    custom_range = request.args.get('custom_range', '')
    
    # Basic stats
    total_violations = Violation.query.count()
    total_students = Student.query.count()
    
    # Category stats
    ringan_violations = Violation.query.filter(Violation.points <= 10).count()
    sedang_violations = Violation.query.filter(Violation.points.between(11, 20)).count()
    berat_violations = Violation.query.filter(Violation.points > 20).count()
    
    # Today's stats
    from datetime import datetime, timedelta
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