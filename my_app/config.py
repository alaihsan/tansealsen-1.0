import os

class Config:
    # Direktori dasar aplikasi (lokasi file config.py ini berada)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Tentukan folder 'instance' secara eksplisit
    INSTANCE_FOLDER = os.path.join(BASE_DIR, 'instance')
    if not os.path.exists(INSTANCE_FOLDER):
        os.makedirs(INSTANCE_FOLDER)
    
    SECRET_KEY = 'kunci_rahasia_yang_sangat_sulit_ditebak_ini_harus_panjang'
    
    # GUNAKAN ABSOLUTE PATH UNTUK DATABASE
    # Ini memastikan database yang dibaca selalu sama, dari mana pun script dijalankan
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(INSTANCE_FOLDER, "site.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Konfigurasi Upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    PER_PAGE = 10