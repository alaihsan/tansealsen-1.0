from my_app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    # KEMBALI KE 'password' AGAR ROUTES.PY TIDAK ERROR
    password = db.Column(db.String(150), nullable=False)
    
    # role = db.Column(db.String(50)) 

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    # students = db.relationship('Student', backref='classroom', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nis = db.Column(db.String(20), unique=True, nullable=False)
    
    # classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'))
    rombel = db.Column(db.String(50)) 

    poin = db.Column(db.Integer, default=100)
    
    violations = db.relationship('Violation', backref='student', lazy=True)

class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    # PERBAIKAN: Ganti 'date' menjadi 'date_posted' agar sesuai dengan routes.py
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)