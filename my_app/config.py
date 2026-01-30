import os

class Config:
    # Mendapatkan direktori absolut dari file ini
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    SECRET_KEY = 'kunci_rahasia_yang_sangat_sulit_ditebak_ini_harus_panjang'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Konfigurasi Upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    PER_PAGE = 10