from datetime import datetime
from my_app.extensions import db
from flask_login import UserMixin

# --- Model Baru: Kelas ---
class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # Contoh: "X IPA 1", "XI IPS 2"
    # Relasi ke murid: Satu kelas memiliki banyak murid
    students = db.relationship('Student', backref='classroom', lazy=True)

    def __repr__(self):
        return f"Classroom('{self.name}')"

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nis = db.Column(db.String(20), unique=True, nullable=False)
    
    # --- Update: Tambahkan Foreign Key ke Kelas ---
    # nullable=True agar murid bisa dibuat tanpa kelas dulu (opsional)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=True)

    # Relasi ke pelanggaran (Kasus ikut murid, tidak peduli dia pindah kelas)
    violations = db.relationship('Violation', backref='student', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Student('{self.name}', '{self.nis}')"

class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    points = db.Column(db.Integer, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)

    def __repr__(self):
        return f"Violation('{self.description}', '{self.points}')"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}')"