import sys
import os

# Tambahkan direktori parent ke sys.path agar bisa import 'my_app' sebagai package
# Ini penting karena kita menggunakan absolute import (e.g. 'from my_app.routes ...')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from my_app.config import Config
from my_app.extensions import db
from my_app.routes import main
from my_app.models import Student 

def create_app():
    # Inisialisasi aplikasi Flask
    app = Flask(__name__)
    
    # Memuat konfigurasi dari objek Config
    app.config.from_object(Config)

    # Inisialisasi ekstensi (seperti database)
    db.init_app(app)

    # Mendaftarkan blueprint (rute-rute aplikasi)
    app.register_blueprint(main)
    
    return app

# Inisialisasi aplikasi
app = create_app()

if __name__ == '__main__':
    # Membuat tabel database jika belum ada
    with app.app_context():
        db.create_all()
    
    # Menjalankan aplikasi dalam mode debug
    app.run(debug=True, host='0.0.0.0', port=5000)