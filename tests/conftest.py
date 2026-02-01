import pytest
from my_app.app import app as flask_app
from my_app.extensions import db
from my_app.models import User

@pytest.fixture
def app():
    """Membuat instance aplikasi dengan konfigurasi testing."""
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret_key"
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Client yang sudah login."""
    # Hapus parameter 'role' agar tidak error
    user = User(username="admin_test")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    client.post('/login', data={
        'username': 'admin_test',
        'password': 'password123'
    }, follow_redirects=True)
    
    return client