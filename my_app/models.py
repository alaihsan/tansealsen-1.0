from my_app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'  # Nama tabel eksplisit (jamak)
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # MySQL password hash butuh panjang cukup
    
    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Classroom(db.Model):
    __tablename__ = 'classrooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    # Cascade delete: Jika kelas dihapus, murid di dalamnya bisa jadi yatim piatu atau ikut terhapus (opsional)
    students = db.relationship('Student', backref='classroom', lazy=True)

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nis = db.Column(db.String(20), unique=True, nullable=False)
    
    # Indexing foreign key direkomendasikan di MySQL untuk performa join
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), index=True)
    rombel = db.Column(db.String(50)) 

    poin = db.Column(db.Integer, default=100)
    
    violations = db.relationship('Violation', backref='student', lazy=True)

class Violation(db.Model):
    __tablename__ = 'violations'
    
    id = db.Column(db.Integer, primary_key=True)
    # Menggunakan VARCHAR(2000) aman di MySQL 5.7+
    description = db.Column(db.String(2000), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)

    # Kolom Tambahan
    pasal = db.Column(db.String(255), nullable=True) # Perbesar sedikit untuk jaga-jaga
    kategori_pelanggaran = db.Column(db.String(50), nullable=True, index=True) # Index untuk filtering cepat
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