from datetime import datetime
from my_app.extensions import db

class Pelanggaran(db.Model):
    # Menambahkan extend_existing=True untuk mencegah error "Table already defined"
    # saat script seeding dijalankan (masalah double import context)
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    nama_murid = db.Column(db.String(100), nullable=False)
    kelas = db.Column(db.String(50), nullable=False)
    pasal = db.Column(db.String(100), nullable=False)
    kategori_pelanggaran = db.Column(db.String(50), nullable=False)
    tanggal_kejadian = db.Column(db.String(50), nullable=False) # Format DD/MM/YYYY
    deskripsi = db.Column(db.Text, nullable=True)
    bukti_file = db.Column(db.String(255), nullable=True)
    di_input_oleh = db.Column(db.String(100), nullable=False)
    tanggal_dicatat = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def tanggal_kejadian_date(self):
        try:
            return datetime.strptime(self.tanggal_kejadian, '%d/%m/%Y').date()
        except (ValueError, TypeError):
            return None

    def __repr__(self):
        return f"Pelanggaran('{self.nama_murid}', '{self.pasal}', '{self.tanggal_kejadian}')"

class Student(db.Model):
    # Menambahkan extend_existing=True
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    kelas = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"Student('{self.nama}', '{self.kelas}')"