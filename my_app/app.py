# Import modul yang diperlukan dari Flask dan pustaka lainnya
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid # Untuk menghasilkan nama file unik

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# --- Konfigurasi Aplikasi ---
app.config['SECRET_KEY'] = 'kunci_rahasia_yang_sangat_sulit_ditebak_ini_harus_panjang'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
PER_PAGE = 10 # Menentukan jumlah item per halaman

# Inisialisasi objek database SQLAlchemy
db = SQLAlchemy(app)

# --- Definisi Model Database ---
class Pelanggaran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_murid = db.Column(db.String(100), nullable=False)
    kelas = db.Column(db.String(50), nullable=False)
    pasal = db.Column(db.String(100), nullable=False)
    kategori_pelanggaran = db.Column(db.String(50), nullable=False)
    tanggal_kejadian = db.Column(db.String(50), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    bukti_file = db.Column(db.String(255), nullable=True)
    di_input_oleh = db.Column(db.String(100), nullable=False)
    tanggal_dicatat = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Pelanggaran('{self.nama_murid}', '{self.pasal}', '{self.tanggal_kejadian}')"

# --- Fungsi Pembantu ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Rute Aplikasi ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['logged_in'] = True
            flash('Berhasil login sebagai Admin!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username atau password salah.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))


@app.route('/history/<string:student_name>')
def student_history(student_name):
    if not session.get('logged_in'):
        flash('Anda harus login untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('login'))

    # Ambil semua pelanggaran HANYA untuk murid yang spesifik
    violations = Pelanggaran.query.filter_by(nama_murid=student_name).order_by(Pelanggaran.tanggal_dicatat.desc()).all()

    # Kirim data ke template baru yang akan kita buat
    return render_template('student_history.html', violations=violations, student_name=student_name)
@app.route('/')
def index():
    if not session.get('logged_in'):
        flash('Anda harus login untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('login'))

    # Logika Paging
    page = request.args.get('page', 1, type=int)
    pelanggaran_pagination = Pelanggaran.query.order_by(Pelanggaran.tanggal_dicatat.desc()).paginate(
        page=page, per_page=PER_PAGE
    )
    return render_template('index.html', pelanggaran_pagination=pelanggaran_pagination)

@app.route('/add', methods=['GET', 'POST'])
def add_violation():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        bukti_file_nama = None
        if 'bukti_file' in request.files:
            file = request.files['bukti_file']
            if file and allowed_file(file.filename):
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                bukti_file_nama = filename
            elif file.filename != '' and not allowed_file(file.filename):
                flash('Tipe file tidak diizinkan. Hanya PNG, JPG, JPEG, GIF.', 'danger')
                return redirect(request.url)

        new_pelanggaran = Pelanggaran(
            nama_murid=request.form['nama_murid'],
            kelas=request.form['kelas'],
            pasal=request.form['pasal'],
            kategori_pelanggaran=request.form['kategori_pelanggaran'],
            tanggal_kejadian=request.form['tanggal_kejadian'],
            deskripsi=request.form['deskripsi'],
            di_input_oleh=request.form['di_input_oleh'],
            bukti_file=bukti_file_nama
        )
        try:
            db.session.add(new_pelanggaran)
            db.session.commit()
            flash('Pelanggaran berhasil dicatat!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan saat mencatat pelanggaran: {e}', 'danger')
            return redirect(request.url)

    return render_template('add_violation.html')

@app.route('/delete/<int:violation_id>', methods=['POST'])
def delete_violation(violation_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    pelanggaran = Pelanggaran.query.get_or_404(violation_id)
    try:
        if pelanggaran.bukti_file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], pelanggaran.bukti_file)
            if os.path.exists(file_path):
                os.remove(file_path)
        db.session.delete(pelanggaran)
        db.session.commit()
        flash('Pelanggaran berhasil dihapus!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Terjadi kesalahan saat menghapus pelanggaran: {e}', 'danger')
    return redirect(url_for('index'))

with app.app_context():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)