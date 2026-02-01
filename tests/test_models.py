from my_app.models import User, Student
from my_app.extensions import db

def test_password_hashing(app):
    """Test keamanan password."""
    # Hapus 'role'
    u = User(username='guru_test')
    u.set_password('rahasia')
    
    assert u.check_password('rahasia') is True
    assert u.check_password('salah') is False
    assert u.password_hash != 'rahasia'

def test_create_student(app):
    """Test pembuatan data siswa."""
    # Hapus 'rombel' karena error (field mungkin tidak ada di DB)
    s = Student(name="Ahmad", nis="998877")
    db.session.add(s)
    db.session.commit()

    saved_student = Student.query.filter_by(nis="998877").first()
    assert saved_student is not None
    assert saved_student.name == "Ahmad"