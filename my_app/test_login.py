from app import app
from my_app.models import User
from my_app.extensions import bcrypt

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    print('User:', user)
    if user:
        print('Password check:', bcrypt.check_password_hash(user.password, 'admin'))
    else:
        print('Admin user not found')