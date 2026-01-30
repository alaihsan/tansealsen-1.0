import os
import time
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import current_app
from sqlalchemy import func
from sqlalchemy.types import Date
from extensions import db
from models import Pelanggaran

# PDF generation availability
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# --- File Handling ---
def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file):
    """Save uploaded file and return filename"""
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Add timestamp to avoid conflicts
        timestamp = str(int(time.time()))
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        return filename
    return None

# --- Date Filters ---
def get_date_filter_from_args(args):
    start_date_str = args.get('start_date')
    end_date_str = args.get('end_date')
    custom_range = args.get('custom_range')
    date_range_str = args.get('date_range')
    
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
    elif date_range_str:
        try:
            if " to " in date_range_str:
                parts = date_range_str.split(" to ")
                start_date = datetime.strptime(parts[0], '%Y-%m-%d').date()
                end_date = datetime.strptime(parts[1], '%Y-%m-%d').date()
            else:
                start_date = datetime.strptime(date_range_str, '%Y-%m-%d').date()
                end_date = start_date
        except ValueError:
            pass
    elif start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    return start_date, end_date, custom_range

def apply_date_filter_to_query(query, start_date, end_date):
    if start_date and end_date:
        formatted_date = func.substr(Pelanggaran.tanggal_kejadian, 7, 4) + '-' + \
                         func.substr(Pelanggaran.tanggal_kejadian, 4, 2) + '-' + \
                         func.substr(Pelanggaran.tanggal_kejadian, 1, 2)
        return query.filter(func.cast(formatted_date, Date).between(start_date, end_date))
    return query

# --- Statistics ---
def get_global_statistics():
    try:
        total_ringan = Pelanggaran.query.filter_by(kategori_pelanggaran='Ringan').count()
        total_sedang = Pelanggaran.query.filter_by(kategori_pelanggaran='Sedang').count()
        total_berat = Pelanggaran.query.filter_by(kategori_pelanggaran='Berat').count()
        total_count = total_ringan + total_sedang + total_berat
        
        today_start = datetime.now().date()
        today_query = apply_date_filter_to_query(Pelanggaran.query, today_start, today_start)

        today_ringan = today_query.filter_by(kategori_pelanggaran='Ringan').count()
        today_sedang = today_query.filter_by(kategori_pelanggaran='Sedang').count()
        today_berat = today_query.filter_by(kategori_pelanggaran='Berat').count()
        
        return {
            'total': total_count,
            'ringan': total_ringan, 'sedang': total_sedang, 'berat': total_berat,
            'today_ringan': today_ringan, 'today_sedang': today_sedang, 'today_berat': today_berat,
            'total_today': today_ringan + today_sedang + today_berat,
            'error': None
        }
    except Exception as e:
        return {'total': 0, 'ringan': 0, 'sedang': 0, 'berat': 0, 'error': str(e)}

def get_filtered_statistics(start_date, end_date):
    try:
        query = apply_date_filter_to_query(Pelanggaran.query, start_date, end_date)
        total_ringan = query.filter_by(kategori_pelanggaran='Ringan').count()
        total_sedang = query.filter_by(kategori_pelanggaran='Sedang').count()
        total_berat = query.filter_by(kategori_pelanggaran='Berat').count()
        total_count = total_ringan + total_sedang + total_berat
        return {'total': total_count, 'ringan': total_ringan, 'sedang': total_sedang, 'berat': total_berat, 'error': None}
    except Exception as e:
        return {'total': 0, 'ringan': 0, 'sedang': 0, 'berat': 0, 'error': str(e)}

def get_top_violators(limit=5):
    try:
        today = datetime.now().date()
        month_start = today.replace(day=1)
        query = apply_date_filter_to_query(Pelanggaran.query, month_start, today)

        top_violators = query.with_entities(
            Pelanggaran.nama_murid,
            func.count(Pelanggaran.id).label('count')
        ).group_by(Pelanggaran.nama_murid).order_by(func.count(Pelanggaran.id).desc()).limit(limit).all()

        violators_list = []
        for violator in top_violators:
            latest = Pelanggaran.query.filter_by(nama_murid=violator.nama_murid).order_by(Pelanggaran.tanggal_dicatat.desc()).first()
            violators_list.append({
                'nama_murid': violator.nama_murid,
                'count': violator.count,
                'latest_date': latest.tanggal_dicatat if latest else None
            })
        return violators_list
    except Exception as e:
        print(e)
        return []

# --- Database Operations ---
def create_violation(data_dict):
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
    return Pelanggaran.query.get(violation_id)

# --- Validation ---
def validate_violation_data(data_dict):
    required = ['nama_murid', 'kelas', 'pasal', 'kategori_pelanggaran', 'tanggal_kejadian', 'di_input_oleh']
    errors = []
    for field in required:
        if not data_dict.get(field) or not str(data_dict.get(field)).strip():
            errors.append(f'{field.replace("_", " ").title()} harus diisi!')
        elif field == 'tanggal_kejadian' and data_dict.get(field).strip():
            try:
                datetime.strptime(data_dict[field], '%d/%m/%Y')
            except ValueError:
                errors.append('Format tanggal tidak valid. Gunakan format DD/MM/YYYY')
    return errors

# --- PDF Generation ---
def generate_pdf_content(violations, start_date=None, end_date=None, custom_range=None):
    if PDF_AVAILABLE:
        return generate_real_pdf(violations, start_date, end_date, custom_range)
    else:
        return generate_pdf_html(violations, start_date, end_date, custom_range)

def generate_real_pdf(violations, start_date=None, end_date=None, custom_range=None):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        filter_info = "Semua Data"
        if custom_range:
            filter_info = custom_range.replace('_', ' ').title()
        elif start_date and end_date:
            filter_info = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "LAPORAN PELANGGARAN MURID", 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"Tanggal Cetak: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}", 0, 1, 'C')
        pdf.cell(0, 6, f"Filter: {filter_info}", 0, 1, 'C')
        pdf.cell(0, 6, f"Total Pelanggaran: {len(violations)}", 0, 1, 'C')
        pdf.ln(10)
        
        # Summary
        ringan = sum(1 for v in violations if v.kategori_pelanggaran == 'Ringan')
        sedang = sum(1 for v in violations if v.kategori_pelanggaran == 'Sedang')
        berat = sum(1 for v in violations if v.kategori_pelanggaran == 'Berat')
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Ringkasan Kategori:", 0, 1, 'L')
        pdf.ln(2)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"Ringan: {ringan} pelanggaran", 0, 1, 'L')
        pdf.cell(0, 6, f"Sedang: {sedang} pelanggaran", 0, 1, 'L')
        pdf.cell(0, 6, f"Berat: {berat} pelanggaran", 0, 1, 'L')
        pdf.ln(8)
        
        # Table
        pdf.set_font("Arial", 'B', 8)
        headers = ["No", "Nama Murid", "Kelas", "Pasal", "Kategori", "Tanggal", "Oleh"]
        col_widths = {'No': 10, 'Nama Murid': 45, 'Kelas': 15, 'Pasal': 30, 'Kategori': 20, 'Tanggal': 20, 'Oleh': 30}
        
        for header in headers:
            pdf.cell(col_widths[header], 8, header, 1, 0, 'C')
        pdf.ln()
        
        pdf.set_font("Arial", size=8)
        for i, v in enumerate(violations, 1):
            pdf.cell(col_widths['No'], 6, str(i), 1, 0, 'C')
            pdf.cell(col_widths['Nama Murid'], 6, v.nama_murid[:25], 1, 0, 'L')
            pdf.cell(col_widths['Kelas'], 6, v.kelas[:10], 1, 0, 'L')
            pdf.cell(col_widths['Pasal'], 6, v.pasal[:15], 1, 0, 'L')
            pdf.cell(col_widths['Kategori'], 6, v.kategori_pelanggaran, 1, 0, 'C')
            pdf.cell(col_widths['Tanggal'], 6, v.tanggal_kejadian, 1, 0, 'C')
            pdf.cell(col_widths['Oleh'], 6, v.di_input_oleh[:15], 1, 0, 'L')
            pdf.ln()
        
        pdf_bytes = pdf.output(dest='S')
        return pdf_bytes.encode('latin-1') if isinstance(pdf_bytes, str) else pdf_bytes
    except Exception as e:
        print(f"PDF Error: {e}")
        return generate_pdf_html(violations, start_date, end_date, custom_range).encode('utf-8')

def generate_pdf_html(violations, start_date, end_date, custom_range):
    filter_info = "Semua Data"
    if custom_range:
        filter_info = custom_range.replace("_", " ").title()
    elif start_date and end_date:
        filter_info = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        
    html = f"""
    <html><head><style>
        body {{ font-family: Arial; font-size: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ border: 1px solid #ddd; padding: 6px; text-align: left; }}
        th {{ background: #f2f2f2; }}
    </style></head><body>
    <h1 style="text-align:center;">LAPORAN PELANGGARAN MURID</h1>
    <p style="text-align:center;">Filter: {filter_info} | Total: {len(violations)}</p>
    <table>
        <thead><tr><th>No</th><th>Nama</th><th>Kelas</th><th>Pasal</th><th>Kategori</th><th>Tanggal</th><th>Oleh</th></tr></thead>
        <tbody>
    """
    for i, v in enumerate(violations, 1):
        html += f"<tr><td>{i}</td><td>{v.nama_murid}</td><td>{v.kelas}</td><td>{v.pasal}</td><td>{v.kategori_pelanggaran}</td><td>{v.tanggal_kejadian}</td><td>{v.di_input_oleh}</td></tr>"
    html += "</tbody></table></body></html>"
    return html