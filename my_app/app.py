from flask import Flask
from config import Config
from extensions import db
from routes import main

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

# Membuat instance aplikasi
app = create_app()

if __name__ == '__main__':
    # Membuat tabel database jika belum ada
    with app.app_context():
        db.create_all()
    
    # Menjalankan aplikasi dalam mode debug
    app.run(debug=True, host='0.0.0.0', port=5000)