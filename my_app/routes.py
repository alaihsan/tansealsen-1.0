import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response, current_app
from extensions import db
from models import Pelanggaran
from utils import (
    validate_violation_data, save_uploaded_file, create_violation, get_violation_by_id,
    get_date_filter_from_args, apply_date_filter_to_query,
    get_global_statistics, get_filtered_statistics, get_top_violators,
    generate_pdf_content
)

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if not session.get('logged_in'):
        flash('Anda harus login untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('main.login'))
    
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    date_range_value = request.args.get('date_range', '')
    
    start_date, end_date, custom_range = get_date_filter_from_args(request.args)
    
    base_query = Pelanggaran.query
    if search_query:
        base_query = base_query.filter(
            Pelanggaran.nama_murid.ilike(f'%{search_query}%') |
            Pelanggaran.kelas.ilike(f'%{search_query}%') |
            Pelanggaran.pasal.ilike(f'%{search_query}%') |
            Pelanggaran.deskripsi.ilike(f'%{search_query}%')
        )
    
    base_query = apply_date_filter_to_query(base_query, start_date, end_date)

    total_ringan = base_query.filter_by(kategori_pelanggaran='Ringan').count()
    total_sedang = base_query.filter_by(kategori_pelanggaran='Sedang').count()
    total_berat = base_query.filter_by(kategori_pelanggaran='Berat').count()

    final_query = base_query
    if category_filter in ['Ringan', 'Sedang', 'Berat']:
        final_query = final_query.filter_by(kategori_pelanggaran=category_filter)

    pelanggaran_pagination = final_query.order_by(Pelanggaran.tanggal_dicatat.desc()).paginate(
        page=page, per_page=current_app.config['PER_PAGE']
    )
    
    start_date_str = start_date.strftime('%Y-%m-%d') if start_date else ''
    end_date_str = end_date.strftime('%Y-%m-%d') if end_date else ''

    return render_template('index.html',
                           pelanggaran_pagination=pelanggaran_pagination,
                           search_query=search_query,
                           start_date=start_date_str,
                           end_date=end_date_str,
                           custom_range=custom_range,
                           date_range_value=date_range_value,
                           category_filter=category_filter,
                           total_ringan=total_ringan,
                           total_sedang=total_sedang,
                           total_berat=total_berat)

@main.route('/add', methods=['GET', 'POST'])
def add_violation():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        errors = validate_violation_data(request.form)
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
        
        violation_data = request.form.to_dict()
        violation_data['bukti_file'] = bukti_filename
        
        if create_violation(violation_data):
            flash('Pelanggaran berhasil dicatat!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Terjadi kesalahan saat menyimpan pelanggaran.', 'danger')
            return render_template('add_violation.html', form_data=request.form)
            
    return render_template('add_violation.html', form_data={})

@main.route('/delete/<int:violation_id>', methods=['POST'])
def delete_violation(violation_id):
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    
    pelanggaran = get_violation_by_id(violation_id)
    if not pelanggaran:
        return jsonify({'success': False, 'message': 'Data tidak ditemukan'}), 404

    try:
        if pelanggaran.bukti_file:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pelanggaran.bukti_file)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(pelanggaran)
        db.session.commit()
        flash('Pelanggaran berhasil dihapus.', 'success')
        return jsonify({'success': True, 'message': 'Pelanggaran berhasil dihapus!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Gagal menghapus: {e}'})

@main.route('/history/<string:student_name>')
def student_history(student_name):
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    
    violations = Pelanggaran.query.filter_by(nama_murid=student_name).order_by(Pelanggaran.tanggal_dicatat.desc()).all()
    # Hitung statistik siswa ini
    total_ringan = sum(1 for v in violations if v.kategori_pelanggaran == 'Ringan')
    total_sedang = sum(1 for v in violations if v.kategori_pelanggaran == 'Sedang')
    total_berat = sum(1 for v in violations if v.kategori_pelanggaran == 'Berat')

    return render_template('student_history.html', 
                           violations=violations, 
                           student_name=student_name,
                           total_ringan=total_ringan,
                           total_sedang=total_sedang,
                           total_berat=total_berat)

@main.route('/statistics')
def statistics():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    
    start_date, end_date, custom_range = get_date_filter_from_args(request.args)
    
    if not custom_range and not (start_date and end_date):
        stats_data = get_global_statistics()
    else:
        stats_data = get_filtered_statistics(start_date, end_date)
        today_stats = get_global_statistics() # Get today stats anyway for comparison
        stats_data['today_ringan'] = today_stats['today_ringan']
        stats_data['today_sedang'] = today_stats['today_sedang']
        stats_data['today_berat'] = today_stats['today_berat']

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

    return render_template('statistics.html', stats_data=template_data, top_violators=top_violators)

@main.route('/export_violations_pdf')
def export_violations_pdf():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        start_date, end_date, custom_range = get_date_filter_from_args(request.args)
        query = apply_date_filter_to_query(Pelanggaran.query, start_date, end_date)
        violations = query.order_by(Pelanggaran.tanggal_dicatat.desc()).all()
        
        pdf_content = generate_pdf_content(violations, start_date, end_date, custom_range)
        response = make_response(pdf_content)
        
        filename_date = datetime.now().strftime("%Y%m%d")
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=laporan_pelanggaran_{filename_date}.pdf'
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['username'] = username
            flash('Login berhasil!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Username atau password salah!', 'danger')
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout!', 'info')
    return redirect(url_for('main.login'))

@main.route('/api/today_stats')
def api_today_stats():
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