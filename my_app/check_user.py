from app import app
from my_app.models import User
from my_app.extensions import db, bcrypt

with app.app_context():
    # Check if admin user exists
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        print(f"Admin user exists: {admin_user}")
    else:
        print("No admin user found. Creating...")
        # Create admin user
        hashed_password = bcrypt.generate_password_hash('admin').decode('utf-8')
        admin = User(username='admin', password=hashed_password)
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    
    # Show all users
    all_users = User.query.all()
    print(f"Total users: {len(all_users)}")
    for user in all_users:
        print(f"Username: {user.username}")