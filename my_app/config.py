import os

class Config:
    # Direktori dasar aplikasi
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kunci_rahasia_yang_sangat_sulit_ditebak_ini_harus_panjang'
    
    DB_USERNAME = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASS') or 'B1smillah#1'        
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_NAME = os.environ.get('DB_NAME') or 'tanse_db'
    
    # Format Connection String untuk MySQL
    # mysql+pymysql://username:password@host/databasename
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Konfigurasi engine MySQL untuk memastikan support karakter utf8mb4 (emoji, dll)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }
    
    # Konfigurasi Upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    PER_PAGE = 20