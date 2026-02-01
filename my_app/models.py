from my_app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    
    # role = db.Column(db.String(50)) 

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    students = db.relationship('Student', backref='classroom', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nis = db.Column(db.String(20), unique=True, nullable=False)
    
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'))
    rombel = db.Column(db.String(50)) 

    poin = db.Column(db.Integer, default=100)
    
    violations = db.relationship('Violation', backref='student', lazy=True)

class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)

    # Kolom Tambahan
    pasal = db.Column(db.String(50), nullable=True)
    kategori_pelanggaran = db.Column(db.String(50), nullable=True)
    di_input_oleh = db.Column(db.String(100), nullable=True)
    bukti_file = db.Column(db.String(255), nullable=True)

    # --- PERBAIKAN DISINI ---
    # Property Helper agar 'p.tanggal_kejadian' di HTML bisa membaca 'date_posted'
    @property
    def tanggal_kejadian(self):
        # Mengembalikan tanggal dalam format string "DD/MM/YYYY" (contoh: 01/02/2026)
        if self.date_posted:
            return self.date_posted.strftime('%d/%m/%Y')
        return "-"

    @property
    def tanggal_dicatat(self):
        # Helper untuk student_history.html yang membutuhkan object datetime asli
        return self.date_posted