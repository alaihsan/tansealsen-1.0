from my_app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class School(db.Model):
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relasi
    users = db.relationship('User', backref='school', lazy=True)
    classrooms = db.relationship('Classroom', backref='school', lazy=True)
    students = db.relationship('Student', backref='school', lazy=True)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
    # Role: 'super_admin' (Pemilik App) atau 'school_admin' (Pihak Sekolah)
    role = db.Column(db.String(20), default='school_admin', nullable=False)
    
    # User milik sekolah mana? (Nullable untuk Super Admin)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)
        
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'

class Classroom(db.Model):
    __tablename__ = 'classrooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False) # Tidak unique global, tapi unique per sekolah (logic di routes)
    
    # Link ke Sekolah
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    students = db.relationship('Student', backref='classroom', lazy=True)

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nis = db.Column(db.String(20), nullable=False) # NIS unique per sekolah, bukan global
    
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), index=True)
    rombel = db.Column(db.String(50)) 
    poin = db.Column(db.Integer, default=100)
    
    # Link ke Sekolah (Untuk query cepat tanpa join classroom)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True)
    
    violations = db.relationship('Violation', backref='student', lazy=True)

class Violation(db.Model):
    __tablename__ = 'violations'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(2000), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)

    pasal = db.Column(db.String(255), nullable=True)
    kategori_pelanggaran = db.Column(db.String(50), nullable=True, index=True)
    di_input_oleh = db.Column(db.String(100), nullable=True)
    bukti_file = db.Column(db.String(255), nullable=True)

    @property
    def tanggal_kejadian(self):
        if self.date_posted:
            return self.date_posted.strftime('%d/%m/%Y')
        return "-"

    @property
    def tanggal_dicatat(self):
        return self.date_posted