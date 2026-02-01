from my_app.app import app
from my_app.extensions import db
from my_app.models import User

# Script ini untuk membuat user admin secara manual
with app.app_context():
    db.create_all()  # Pastikan tabel dibuat ulang jika belum ada

    # Cek apakah admin sudah ada
    if not User.query.filter_by(username='admin').first():
        # Buat user baru
        user = User(username='admin')
        user.set_password('password123')  # Password default: password123
        
        # Uncomment baris di bawah ini HANYA jika Anda sudah mengaktifkan kolom role di models.py
        # user.role = 'admin' 
        
        db.session.add(user)
        db.session.commit()
        print("✅ User 'admin' berhasil dibuat dengan password 'password123'")
    else:
        print("ℹ️ User 'admin' sudah ada di database.")