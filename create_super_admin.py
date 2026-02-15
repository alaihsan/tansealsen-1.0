from my_app.app import app
from my_app.extensions import db
from my_app.models import User, School

# Script ini akan MENGHAPUS database lama dan membuat yang baru
# Jalankan hanya saat inisialisasi awal!

with app.app_context():
    print("⚠️  Menghapus database lama...")
    db.drop_all()
    print("✅  Membuat tabel baru...")
    db.create_all()

    # 1. Buat Akun Super Admin (Tanpa Sekolah)
    super_admin = User(username='superadmin', role='super_admin')
    super_admin.set_password('super123') # Ganti password ini nanti
    db.session.add(super_admin)
    
    # 2. Buat Sekolah Contoh (Demo)
    sekolah_demo = School(name='SMP Al-Ihsan (Demo)', address='Jl. Inpres No. 22')
    db.session.add(sekolah_demo)
    db.session.flush() # Agar kita dapat ID sekolah

    # 3. Buat Admin untuk Sekolah Demo
    school_admin = User(username='admin_demo', role='school_admin', school_id=sekolah_demo.id)
    school_admin.set_password('admin123')
    db.session.add(school_admin)

    db.session.commit()
    
    print("="*40)
    print("✅ SETUP BERHASIL")
    print("="*40)
    print("1. Login Super Admin:")
    print("   User: superadmin | Pass: super123")
    print("-" * 20)
    print("2. Login Sekolah Demo:")
    print("   User: admin_demo | Pass: admin123")
    print("="*40)