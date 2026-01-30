# Import modul yang diperlukan dari Flask dan pustaka lainnya
import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, case
from sqlalchemy.types import Date

# PDF generation availability
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# --- Konfigurasi Aplikasi ---
app.config['SECRET_KEY'] = 'kunci_rahasia_yang_sangat_sulit_ditebak_ini_harus_panjang'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
PER_PAGE = 10

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """Save uploaded file and return filename"""
    if file and file.filename and allowed_file(file.filename):
        # Generate secure filename
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        
        # Add timestamp to avoid conflicts
        import time
        timestamp = str(int(time.time()))
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        return filename
    return None

# Inisialisasi objek database SQLAlchemy
db = SQLAlchemy(app)

# --- Definisi Model Database ---
class Pelanggaran(db.Model):
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

# --- Helper Functions ---
def _get_date_filter_from_args(args):
    """Mendapatkan filter tanggal dari argumen request."""
    start_date_str = args.get('start_date')
    end_date_str = args.get('end_date')
    custom_range = args.get('custom_range')
    
    start_date, end_date = None, None
    today = datetime.now().date()

    if custom_range:
        if custom_range == 'today':
            start_date = end_date = today
        elif custom_range == 'this_week':
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif custom_range == 'this_month':
            start_date = today.replace(day=1)
            end_date = today
        elif custom_range == 'last_7_days':
            start_date = today - timedelta(days=6)
            end_date = today
    elif start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass # Abaikan jika format salah

    return start_date, end_date, custom_range

def _apply_date_filter_to_query(query, start_date, end_date):
    """
    Menerapkan filter tanggal ke query SQLAlchemy.
    Ini mengatasi masalah tanggal yang disimpan sebagai string DD/MM/YYYY.
    """
    if start_date and end_date:
        # Konstruksi tanggal yang bisa dibandingkan oleh SQLite (YYYY-MM-DD)
        # dengan memanipulasi string.
        formatted_date = func.substr(Pelanggaran.tanggal_kejadian, 7, 4) + '-' + \
                         func.substr(Pelanggaran.tanggal_kejadian, 4, 2) + '-' + \
                         func.substr(Pelanggaran.tanggal_kejadian, 1, 2)
        
        # Casting ke tipe Date untuk perbandingan yang benar
        return query.filter(func.cast(formatted_date, Date).between(start_date, end_date))
    return query

def get_global_statistics():
    """Menghitung statistik global untuk semua kategori pelanggaran"""
    try:
        total_ringan = Pelanggaran.query.filter_by(kategori_pelanggaran='Ringan').count()
        total_sedang = Pelanggaran.query.filter_by(kategori_pelanggaran='Sedang').count()
        total_berat = Pelanggaran.query.filter_by(kategori_pelanggaran='Berat').count()
        total_count = total_ringan + total_sedang + total_berat
        
        # Today's statistics
        today_start = datetime.now().date()
        today_end = today_start
        today_query = _apply_date_filter_to_query(Pelanggaran.query, today_start, today_end)

        today_ringan = today_query.filter_by(kategori_pelanggaran='Ringan').count()
        today_sedang = today_query.filter_by(kategori_pelanggaran='Sedang').count()
        today_berat = today_query.filter_by(kategori_pelanggaran='Berat').count()
        
        return {
            'total': total_count,
            'ringan': total_ringan,
            'sedang': total_sedang,
            'berat': total_berat,
            'today_ringan': today_ringan,
            'today_sedang': today_sedang,
            'today_berat': today_berat,
            'total_today': today_ringan + today_sedang + today_berat,
            'error': None
        }
    except Exception as e:
        return {
            'total': 0, 'ringan': 0, 'sedang': 0, 'berat': 0,
            'today_ringan': 0, 'today_sedang': 0, 'today_berat': 0,
            'total_today': 0, 'error': str(e)
        }

def get_filtered_statistics(start_date, end_date):
    """Menghitung statistik untuk filter yang sudah diterapkan"""
    try:
        query = _apply_date_filter_to_query(Pelanggaran.query, start_date, end_date)
        
        total_ringan = query.filter_by(kategori_pelanggaran='Ringan').count()
        total_sedang = query.filter_by(kategori_pelanggaran='Sedang').count()
        total_berat = query.filter_by(kategori_pelanggaran='Berat').count()
        total_count = total_ringan + total_sedang + total_berat
        
        return {
            'total': total_count,
            'ringan': total_ringan,
            'sedang': total_sedang,
            'berat': total_berat,
            'error': None
        }
    except Exception as e:
        return { 'total': 0, 'ringan': 0, 'sedang': 0, 'berat': 0, 'error': str(e) }

def get_top_violators(limit=5):
    """Mendapatkan daftar murid dengan pelanggaran terbanyak bulan ini"""
    try:
        today = datetime.now().date()
        month_start = today.replace(day=1)
        
        # Query untuk mendapatkan top violators
        query = _apply_date_filter_to_query(Pelanggaran.query, month_start, today)

        top_violators = query.with_entities(
            Pelanggaran.nama_murid,
            func.count(Pelanggaran.id).label('count')
        ).group_by(
            Pelanggaran.nama_murid
        ).order_by(
            func.count(Pelanggaran.id).desc()
        ).limit(limit).all()

        # Untuk mendapatkan tanggal terakhir, kita perlu query tambahan
        violators_list = []
        for violator in top_violators:
            latest_violation = Pelanggaran.query.filter_by(nama_murid=violator.nama_murid).order_by(Pelanggaran.tanggal_dicatat.desc()).first()
            violators_list.append({
                'nama_murid': violator.nama_murid,
                'count': violator.count,
                'latest_date': latest_violation.tanggal_dicatat if latest_violation else None
            })
        
        return violators_list
    except Exception as e:
        print(e)
        return []

# --- Database Operations ---
def create_violation(data_dict):
    """Membuat entri baru ke database"""
    try:
        new_violation = Pelanggaran(
            nama_murid=data_dict['nama_murid'],
            kelas=data_dict['kelas'],
            pasal=data_dict['pasal'],
            kategori_pelanggaran=data_dict['kategori_pelanggaran'],
            tanggal_kejadian=data_dict['tanggal_kejadian'],
            deskripsi=data_dict.get('deskripsi', ''),
            di_input_oleh=data_dict['di_input_oleh'],
            bukti_file=data_dict.get('bukti_file')
        )
        db.session.add(new_violation)
        db.session.commit()
        return new_violation
    except Exception as e:
        db.session.rollback()
        return None



def get_violation_by_id(violation_id):
    """Ambil data pelanggaran berdasarkan ID"""
    return Pelanggaran.query.get(violation_id)

def update_violation(violation_id, data_dict):
    """Update data pelanggaran yang sudah ada"""
    try:
        pelanggaran = Pelanggaran.query.get(violation_id)
        if pelanggaran:
            for key, value in data_dict.items():
                setattr(pelanggaran, key, value)
        
        db.session.commit()
        return pelanggaran
    except Exception as e:
        db.session.rollback()
        return None

# --- Validasi ---
def validate_violation_data(data_dict):
    """Validasi data pelanggaran sebelum disimpan"""
    required_fields = ['nama_murid', 'kelas', 'pasal', 'kategori_pelanggaran', 'tanggal_kejadian', 'di_input_oleh']
    
    errors = []
    
    for field in required_fields:
        if not data_dict.get(field) or not str(data_dict.get(field)).strip():
            errors.append(f'{field.replace("_", " ").title()} harus diisi!')
        elif field == 'tanggal_kejadian' and data_dict.get(field).strip():
            try:
                datetime.strptime(data_dict[field], '%d/%m/%Y')
            except ValueError:
                errors.append('Format tanggal tidak valid. Gunakan format DD/MM/YYYY')
        elif field == 'kategori_pelanggaran' and data_dict.get(field) not in ['Ringan', 'Sedang', 'Berat']:
            errors.append('Kategori pelanggaran harus salah satu dari: Ringan, Sedang, Berat')
    
    return errors

# --- Rute API ---
@app.route('/')
def index():
    """Halaman utama dengan daftar pelanggaran"""
    if not session.get('logged_in'):
        flash('Anda harus login untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    
    start_date, end_date, custom_range = _get_date_filter_from_args(request.args)
    
    query = Pelanggaran.query
    
    if search_query:
        query = query.filter(
            Pelanggaran.nama_murid.ilike(f'%{search_query}%') |
            Pelanggaran.kelas.ilike(f'%{search_query}%') |
            Pelanggaran.pasal.ilike(f'%{search_query}%') |
            Pelanggaran.deskripsi.ilike(f'%{search_query}%')
        )
    
    query = _apply_date_filter_to_query(query, start_date, end_date)

    # Hitung statistik ringkasan berdasarkan query yang sudah difilter
    total_ringan = query.filter_by(kategori_pelanggaran='Ringan').count()
    total_sedang = query.filter_by(kategori_pelanggaran='Sedang').count()
    total_berat = query.filter_by(kategori_pelanggaran='Berat').count()

    pelanggaran_pagination = query.order_by(Pelanggaran.tanggal_dicatat.desc()).paginate(
        page=page, per_page=PER_PAGE
    )
    
    start_date_str = start_date.strftime('%Y-%m-%d') if start_date else ''
    end_date_str = end_date.strftime('%Y-%m-%d') if end_date else ''

    return render_template('index.html',
                           pelanggaran_pagination=pelanggaran_pagination,
                           search_query=search_query,
                           start_date=start_date_str,
                           end_date=end_date_str,
                           custom_range=custom_range,
                           total_ringan=total_ringan,
                           total_sedang=total_sedang,
                           total_berat=total_berat)

# --- Rute Tambah Pelanggaran ---
@app.route('/add', methods=['GET', 'POST'])
def add_violation():
    """Halaman untuk menambah pelanggaran baru"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        errors = validate_violation_data(request.form)
        
        # Handle file upload
        bukti_filename = None
        if 'bukti_file' in request.files:
            file = request.files['bukti_file']
            if file.filename != '':
                bukti_filename = save_uploaded_file(file)
                if not bukti_filename:
                    errors.append('Format file tidak didukung. Gunakan PNG, JPG, atau GIF.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('add_violation.html', form_data=request.form)
        
        # Create violation data with file info
        violation_data = request.form.to_dict()
        violation_data['bukti_file'] = bukti_filename
        
        new_violation = create_violation(violation_data)
        if new_violation:
            flash('Pelanggaran berhasil dicatat!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Terjadi kesalahan saat menyimpan pelanggaran.', 'danger')
            return render_template('add_violation.html', form_data=request.form)
            
    return render_template('add_violation.html', form_data={})

# --- Rute Hapus Pelanggaran ---
@app.route('/delete/<int:violation_id>', methods=['POST'])
def delete_violation(violation_id):
    """Hapus pelanggaran dari database"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    pelanggaran = get_violation_by_id(violation_id)
    if not pelanggaran:
        return jsonify({'success': False, 'message': 'Data tidak ditemukan'}), 404

    try:
        if pelanggaran.bukti_file:
            try:
                file_path = os.path.join(UPLOAD_FOLDER, pelanggaran.bukti_file)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                # Log error penghapusan file jika perlu, tapi jangan hentikan proses
                print(f"Error deleting file {pelanggaran.bukti_file}: {e}")

        db.session.delete(pelanggaran)
        db.session.commit()
        flash('Pelanggaran berhasil dihapus.', 'success')
        return jsonify({'success': True, 'message': 'Pelanggaran berhasil dihapus!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Gagal menghapus: {e}'})

# --- Rute Riwayat Siswa ---
@app.route('/history/<string:student_name>')
def student_history(student_name):
    """Halaman riwayat pelanggaran per siswa"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    violations = Pelanggaran.query.filter_by(nama_murid=student_name).order_by(Pelanggaran.tanggal_dicatat.desc()).all()
    
    return render_template('student_history.html', violations=violations, student_name=student_name)



# --- Rute Statistik ---
@app.route('/statistics')
def statistics():
    """Halaman statistik pelanggaran"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    start_date, end_date, custom_range = _get_date_filter_from_args(request.args)
    
    # Jika tidak ada filter, tampilkan statistik global
    if not custom_range and not (start_date and end_date):
        stats_data = get_global_statistics()
    else:
        # Jika ada filter, hitung statistik berdasarkan rentang tersebut
        stats_data = get_filtered_statistics(start_date, end_date)
        # Tambahkan kembali data today untuk perbandingan
        today_stats = get_global_statistics()
        stats_data['today_ringan'] = today_stats['today_ringan']
        stats_data['today_sedang'] = today_stats['today_sedang']
        stats_data['today_berat'] = today_stats['today_berat']

    # Data untuk dikirim ke template
    template_data = {
        'total': stats_data.get('total', 0),
        'ringan': stats_data.get('ringan', 0),
        'sedang': stats_data.get('sedang', 0),
        'berat': stats_data.get('berat', 0),
        'today_ringan': stats_data.get('today_ringan', 0),
        'today_sedang': stats_data.get('today_sedang', 0),
        'today_berat': stats_data.get('today_berat', 0),
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
        'custom_range': custom_range,
        'error': stats_data.get('error')
    }

    top_violators = get_top_violators()
    
    if template_data['error']:
        flash(f"Terjadi kesalahan saat menghitung statistik: {template_data['error']}", 'danger')

    return render_template('statistics.html', 
                         stats_data=template_data, 
                         top_violators=top_violators)

# --- Helper untuk format ---
def format_date_for_display(date_obj):
    """Format tanggal untuk display"""
    if isinstance(date_obj, datetime) or isinstance(date_obj, date):
        return date_obj.strftime('%d %b %Y')
    return ''
    
def format_date_for_db(date_str):
    """Format tanggal untuk database"""
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except (ValueError, TypeError):
        return None

# --- Export Functions ---
@app.route('/export_violations_pdf')
def export_violations_pdf():
    """Export violations to PDF with current filters"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        start_date, end_date, custom_range = _get_date_filter_from_args(request.args)
        query = _apply_date_filter_to_query(Pelanggaran.query, start_date, end_date)
        violations = query.order_by(Pelanggaran.tanggal_dicatat.desc()).all()
        
        pdf_content = generate_pdf_content(violations, start_date, end_date, custom_range)
        
        response = make_response(pdf_content)
        filename_date = datetime.now().strftime("%Y%m%d")
        
        if PDF_AVAILABLE:
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=laporan_pelanggaran_{filename_date}.pdf'
        else:
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=laporan_pelanggaran_{filename_date}.html'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export_violations_list')
def export_violations_list():
    """Export violations as JSON for detailed list export"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        start_date, end_date, custom_range = _get_date_filter_from_args(request.args)
        query = _apply_date_filter_to_query(Pelanggaran.query, start_date, end_date)
        violations = query.order_by(Pelanggaran.tanggal_dicatat.desc()).all()
        
        violations_data = [{
            'nama_murid': v.nama_murid, 'kelas': v.kelas, 'pasal': v.pasal,
            'kategori_pelanggaran': v.kategori_pelanggaran, 'tanggal_kejadian': v.tanggal_kejadian,
            'deskripsi': v.deskripsi or '', 'di_input_oleh': v.di_input_oleh,
            'tanggal_dicatat': v.tanggal_dicatat.strftime('%d/%m/%Y %H:%M') if v.tanggal_dicatat else ''
        } for v in violations]
        
        filter_info = "Semua Data"
        if custom_range:
            filter_info = custom_range.replace('_', ' ').title()
        elif start_date and end_date:
            filter_info = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        
        return jsonify({
            'violations': violations_data,
            'filter_info': filter_info,
            'total': len(violations_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_pdf_content(violations, start_date=None, end_date=None, custom_range=None):
    """Generate PDF content for violations"""
    
    if PDF_AVAILABLE:
        return generate_real_pdf(violations, start_date, end_date, custom_range)
    else:
        return generate_pdf_html(violations, start_date, end_date, custom_range)

def generate_real_pdf(violations, start_date=None, end_date=None, custom_range=None):
    """Generate real PDF using fpdf2"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Build filter info
        filter_info = "Semua Data"
        if custom_range:
            filter_info = custom_range.replace('_', ' ').title()
        elif start_date and end_date:
            filter_info = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        
        # Header
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "LAPORAN PELANGGARAN MURID", 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"Tanggal Cetak: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}", 0, 1, 'C')
        pdf.cell(0, 6, f"Filter: {filter_info}", 0, 1, 'C')
        pdf.cell(0, 6, f"Total Pelanggaran: {len(violations)}", 0, 1, 'C')
        pdf.ln(10)
        
        # Category summary
        ringan_count = sum(1 for v in violations if v.kategori_pelanggaran == 'Ringan')
        sedang_count = sum(1 for v in violations if v.kategori_pelanggaran == 'Sedang')
        berat_count = sum(1 for v in violations if v.kategori_pelanggaran == 'Berat')
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Ringkasan Kategori:", 0, 1, 'L')
        pdf.ln(2)
        
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"Ringan: {ringan_count} pelanggaran", 0, 1, 'L')
        pdf.cell(0, 6, f"Sedang: {sedang_count} pelanggaran", 0, 1, 'L')
        pdf.cell(0, 6, f"Berat: {berat_count} pelanggaran", 0, 1, 'L')
        pdf.ln(8)
        
        # Table headers
        pdf.set_font("Arial", 'B', 8)
        headers = ["No", "Nama Murid", "Kelas", "Pasal", "Kategori", "Tanggal", "Oleh"]
        col_widths = {'No': 10, 'Nama Murid': 45, 'Kelas': 15, 'Pasal': 30, 'Kategori': 20, 'Tanggal': 20, 'Oleh': 30}
        
        for header in headers:
            pdf.cell(col_widths[header], 8, header, 1, 0, 'C')
        pdf.ln()
        
        # Table data
        pdf.set_font("Arial", size=8)
        for i, violation in enumerate(violations, 1):
            pdf.cell(col_widths['No'], 6, str(i), 1, 0, 'C')
            pdf.cell(col_widths['Nama Murid'], 6, violation.nama_murid[:25], 1, 0, 'L')
            pdf.cell(col_widths['Kelas'], 6, violation.kelas[:10], 1, 0, 'L')
            pdf.cell(col_widths['Pasal'], 6, violation.pasal[:15], 1, 0, 'L')
            pdf.cell(col_widths['Kategori'], 6, violation.kategori_pelanggaran, 1, 0, 'C')
            pdf.cell(col_widths['Tanggal'], 6, violation.tanggal_kejadian, 1, 0, 'C')
            pdf.cell(col_widths['Oleh'], 6, violation.di_input_oleh[:15], 1, 0, 'L')
            pdf.ln()
            
            # Deskripsi jika ada
            if violation.deskripsi:
                pdf.set_font("Arial", 'I', 7)
                pdf.set_text_color(100, 100, 100)
                pdf.multi_cell(sum(col_widths.values()), 4, f"   Deskripsi: {violation.deskripsi}", 0, 'L')
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Arial", size=8)


        # Footer
        pdf.ln(10)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 6, "Laporan ini dihasilkan otomatis oleh Sistem Manajemen Pelanggaran Murid", 0, 1, 'C')
        pdf.cell(0, 6, f"© Tim IT Alsen 22 - {datetime.now().year}", 0, 1, 'C')
        
        pdf_bytes = pdf.output(dest='S')
        return pdf_bytes.encode('latin-1') if isinstance(pdf_bytes, str) else pdf_bytes
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        return generate_pdf_html(violations, start_date, end_date, custom_range).encode('utf-8')

def generate_pdf_html(violations, start_date=None, end_date=None, custom_range=None):
    """Generate HTML content for PDF export"""
    
    # Build filter info
    filter_info = "Semua Data"
    if custom_range:
        filter_info = custom_range.replace("_", " ").title()
    elif start_date and end_date:
        filter_info = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Laporan Pelanggaran</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; font-size: 10px; color: #333; }}
        .header {{ text-align: center; margin-bottom: 20px; border-bottom: 1px solid #ccc; padding-bottom: 15px;}}
        .header h1 {{ margin-bottom: 5px; }}
        .header p {{ color: #555; margin: 2px 0; }}
        .info {{ background: #f9f9f9; padding: 10px; border: 1px solid #eee; border-radius: 5px; margin-bottom: 20px; }}
        .table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .table th, .table td {{ border: 1px solid #ddd; padding: 6px; text-align: left; }}
        .table th {{ background: #f2f2f2; font-weight: bold; }}
        .table tr:nth-child(even) {{ background: #f9f9f9; }}
        .footer {{ margin-top: 20px; text-align: center; color: #777; font-size: 9px; }}
        .category-ringan {{ color: #28a745; }}
        .category-sedang {{ color: #fd7e14; }}
        .category-berat {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>LAPORAN PELANGGARAN MURID</h1>
        <p>Tanggal Cetak: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}</p>
        <p>Filter: {filter_info}</p>
        <p>Total Pelanggaran: {len(violations)}</p>
    </div>
    
    <div class="info">
        <strong>Ringkasan Kategori:</strong><br>
        - Ringan: {sum(1 for v in violations if v.kategori_pelanggaran == 'Ringan')} pelanggaran<br>
        - Sedang: {sum(1 for v in violations if v.kategori_pelanggaran == 'Sedang')} pelanggaran<br>
        - Berat: {sum(1 for v in violations if v.kategori_pelanggaran == 'Berat')} pelanggaran
    </div>
    
    <table class="table">
        <thead>
            <tr>
                <th>No</th>
                <th>Nama Murid</th>
                <th>Kelas</th>
                <th>Pasal</th>
                <th>Kategori</th>
                <th>Tanggal</th>
                <th>Deskripsi</th>
                <th>Diinput Oleh</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for i, violation in enumerate(violations, 1):
        category_class = f"category-{violation.kategori_pelanggaran.lower()}"
        html += f"""
            <tr>
                <td>{i}</td>
                <td>{violation.nama_murid}</td>
                <td>{violation.kelas}</td>
                <td>{violation.pasal}</td>
                <td class="{category_class}">{violation.kategori_pelanggaran}</td>
                <td>{violation.tanggal_kejadian}</td>
                <td>{violation.deskripsi or '-'}</td>
                <td>{violation.di_input_oleh}</td>
            </tr>
        """
    
    html += """
        </tbody>
    </table>
    
    <div class="footer">
        <p>Laporan ini dihasilkan otomatis oleh Sistem Manajemen Pelanggaran Murid.</p>
        <p>© Tim IT Alsen 22 - {datetime.now().year}</p>
    </div>
</body>
</html>
    """
    
    return html

# --- Security ---
def hash_password(password):
    """Hash password menggunakan Werkzeug"""
    return generate_password_hash(password)

def get_user_by_credentials(username, password):
    """Autentikasi user dengan credentials"""
    return None  # Placeholder for authentication

def verify_password_hash(hashed_password, user_password):
    """Verifikasi password hash"""
    return check_password_hash(hashed_password, user_password)

# --- Rute Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple hardcoded authentication
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['username'] = username
            flash('Login berhasil!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username atau password salah!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Anda telah logout!', 'info')
    return redirect(url_for('login'))

# --- API Endpoints ---
@app.route('/api/today_stats')
def api_today_stats():
    """API endpoint untuk mendapatkan statistik hari ini"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        today_stats = get_global_statistics()
        return jsonify({
            'ringan': today_stats['today_ringan'],
            'sedang': today_stats['today_sedang'],
            'berat': today_stats['today_berat'],
            'total': today_stats['total_today']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Main execution ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)