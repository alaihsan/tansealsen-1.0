from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# Inisialisasi object SQLAlchemy
# Kita belum bind ke app di sini, nanti di app.py
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
