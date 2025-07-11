# Import modul yang diperlukan dari Flask dan pustaka lainnya
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid # Untuk menghasilkan nama file unik

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# --- Konfigurasi Aplikasi ---
# SECRET_KEY sangat penting untuk keamanan sesi Flask
# Ubah ini dengan string acak yang kuat di aplikasi produksi!
app.config['SECRET_KEY'] = 'kunci_rahasia_yang_sangat_sulit_ditebak_ini_harus_panjang' 

# Konfigurasi database SQLite. Database akan disimpan dalam file 'site.db' di folder instance.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# Menonaktifkan pelacakan modifikasi SQLAlchemy untuk menghemat memori
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Konfigurasi folder untuk menyimpan file yang diunggah
# Pastikan folder 'uploads' ada di dalam folder 'static'
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Batasi ukuran file yang diizinkan (misal: 16 MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
# Tipe file yang diizinkan untuk diunggah
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Inisialisasi objek database SQLAlchemy
db = SQLAlchemy(app)

# --- Definisi Model Database ---
# Kelas 'Pelanggaran' merepresentasikan tabel 'pelanggaran' di database
class Pelanggaran(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Kolom ID utama
    nama_murid = db.Column(db.String(100), nullable=False) # Nama murid, tidak boleh kosong
    jenis_pelanggaran = db.Column(db.String(100), nullable=False) # Jenis pelanggaran, tidak boleh kosong
    tanggal = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Tanggal dan waktu pelanggaran, default waktu sekarang
    deskripsi = db.Column(db.Text, nullable=True) # Deskripsi pelanggaran, boleh kosong
    bukti_file = db.Column(db.String(255), nullable=True) # Nama file bukti, boleh kosong

    # Representasi string dari objek Pelanggaran (untuk debugging)
    def __repr__(self):
        return f"Pelanggaran('{self.nama_murid}', '{self.jenis_pelanggaran}', '{self.tanggal}')"

# --- Fungsi Pembantu untuk Upload File ---
# Memeriksa apakah ekstensi file diizinkan
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Rute Aplikasi ---

# Rute login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Jika sudah login, redirect ke halaman utama
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Cek username dan password (hardcoded untuk contoh ini)
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            flash('Berhasil login sebagai Admin!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username atau password salah.', 'danger')
    
    return render_template('login.html')

# Rute logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Hapus status login dari sesi
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

# Rute utama: Menampilkan daftar semua pelanggaran
@app.route('/')
def index():
    # Memeriksa apakah pengguna sudah login
    if not session.get('logged_in'):
        flash('Anda harus login untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('login'))

    # Mengambil semua data pelanggaran dari database, diurutkan berdasarkan tanggal terbaru
    pelanggaran = Pelanggaran.query.order_by(Pelanggaran.tanggal.desc()).all()
    # Merender template 'index.html' dan mengirimkan data pelanggaran ke sana
    return render_template('index.html', pelanggaran=pelanggaran)

# Rute untuk menambah pelanggaran baru
@app.route('/add', methods=['GET', 'POST'])
def add_violation():
    # Memeriksa apakah pengguna sudah login
    if not session.get('logged_in'):
        flash('Anda harus login untuk menambah pelanggaran.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Mengambil data dari form
        nama_murid = request.form['nama_murid']
        jenis_pelanggaran = request.form['jenis_pelanggaran']
        deskripsi = request.form['deskripsi']
        
        bukti_file_nama = None # Inisialisasi nama file bukti
        
        # Memeriksa apakah ada file yang diunggah
        if 'bukti_file' in request.files:
            file = request.files['bukti_file']
            # Jika file ada dan nama filenya tidak kosong (artinya file dipilih)
            if file and allowed_file(file.filename):
                # Membuat nama file unik menggunakan UUID
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                # Menyimpan file ke folder UPLOAD_FOLDER
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                bukti_file_nama = filename
            elif file.filename == '':
                # Jika input file kosong (tidak ada file yang dipilih)
                flash('Tidak ada file bukti yang dipilih.', 'warning')
            else:
                # Jika tipe file tidak diizinkan
                flash('Tipe file tidak diizinkan. Hanya PNG, JPG, JPEG, GIF.', 'danger')
                return redirect(request.url) # Kembali ke halaman form

        # Membuat objek Pelanggaran baru
        new_pelanggaran = Pelanggaran(
            nama_murid=nama_murid,
            jenis_pelanggaran=jenis_pelanggaran,
            deskripsi=deskripsi,
            bukti_file=bukti_file_nama
        )

        try:
            # Menambahkan objek ke sesi database dan melakukan commit
            db.session.add(new_pelanggaran)
            db.session.commit()
            flash('Pelanggaran berhasil dicatat!', 'success')
            return redirect(url_for('index')) # Redirect ke halaman utama
        except Exception as e:
            # Menangani error jika ada masalah saat menyimpan ke database
            db.session.rollback() # Rollback perubahan jika ada error
            flash(f'Terjadi kesalahan saat mencatat pelanggaran: {e}', 'danger')
            return redirect(request.url) # Kembali ke halaman form

    # Jika metode GET, tampilkan form
    return render_template('add_violation.html')

# Rute untuk menghapus pelanggaran
@app.route('/delete/<int:violation_id>', methods=['POST'])
def delete_violation(violation_id):
    # Memastikan pengguna sudah login sebelum menghapus
    if not session.get('logged_in'):
        flash('Anda harus login untuk menghapus pelanggaran.', 'danger')
        return redirect(url_for('login'))

    # Mencari pelanggaran berdasarkan ID
    pelanggaran = Pelanggaran.query.get_or_404(violation_id)

    try:
        # Hapus file bukti jika ada
        if pelanggaran.bukti_file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], pelanggaran.bukti_file)
            if os.path.exists(file_path):
                os.remove(file_path)
                flash(f'File bukti {pelanggaran.bukti_file} berhasil dihapus.', 'info')
            else:
                flash(f'File bukti {pelanggaran.bukti_file} tidak ditemukan di server.', 'warning')

        # Hapus entri dari database
        db.session.delete(pelanggaran)
        db.session.commit()
        flash('Pelanggaran berhasil dihapus!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Terjadi kesalahan saat menghapus pelanggaran: {e}', 'danger')
    
    return redirect(url_for('index'))

# --- Inisialisasi Database ---
# Ini akan membuat file database dan tabel jika belum ada
# Pastikan ini dijalankan hanya sekali atau saat pertama kali aplikasi dijalankan
with app.app_context():
    # Membuat folder uploads jika belum ada
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    db.create_all()

# Menjalankan aplikasi Flask
if __name__ == '__main__':
    # app.run(debug=True) akan otomatis me-reload server saat ada perubahan kode
    # dan menampilkan pesan error yang lebih detail.
    app.run(debug=True)
