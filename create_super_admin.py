from my_app.app import app
from my_app.extensions import db
from my_app.models import User, School, ViolationCategory, ViolationRule, ViolationPhoto

# Script RESET DATABASE dengan struktur baru
with app.app_context():
    print("⏳ Menghapus database lama...")
    db.drop_all()
    print("⏳ Membuat tabel baru (termasuk ViolationPhoto)...")
    db.create_all()

    # 1. Super Admin
    super_admin = User(username='superadmin', role='super_admin', full_name="Super Administrator")
    super_admin.set_password('super123') 
    db.session.add(super_admin)
    
    # 2. Sekolah Demo
    sekolah = School(name='Sekolah Demo Alsen', address='Jl. Contoh No. 1')
    db.session.add(sekolah)
    db.session.flush()

    # 3. Admin Sekolah Demo
    admin_demo = User(username='admin_demo', role='school_admin', school_id=sekolah.id, full_name="Pak Admin Sekolah")
    admin_demo.set_password('admin123')
    db.session.add(admin_demo)

    # 4. Data Default (Kategori & Pasal)
    cats = [('Ringan', 5), ('Sedang', 15), ('Berat', 30)]
    for n, p in cats:
        db.session.add(ViolationCategory(name=n, points=p, school_id=sekolah.id))
        
    rules = [('Pasal 1', 'Pelanggaran Seragam'), ('Pasal 2', 'Terlambat Datang')]
    for c, d in rules:
        db.session.add(ViolationRule(code=c, description=d, school_id=sekolah.id))

    db.session.commit()
    print("✅ SETUP BERHASIL! TABEL FOTO SUDAH DITAMBAHKAN.")