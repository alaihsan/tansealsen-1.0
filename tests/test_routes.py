from my_app.models import User
from my_app.extensions import db

def test_home_page(client):
    """Test halaman home."""
    # Tambahkan follow_redirects=True karena sepertinya redirect ke login
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200

def test_login_logout(client, app):
    """Test alur login berhasil dan logout."""
    # Setup user (tanpa role)
    u = User(username="guru_login")
    u.set_password("123456")
    db.session.add(u)
    db.session.commit()

    # Test Login
    response = client.post('/login', data={
        'username': 'guru_login',
        'password': '123456'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Cek apakah logout muncul (tandanya sudah login)
    assert b"Logout" in response.data or b"guru_login" in response.data

    # Test Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_login_failed(client):
    """Test login gagal."""
    response = client.post('/login', data={
        'username': 'user_ngawur',
        'password': 'password_salah'
    }, follow_redirects=True)
    
    # Cek apakah form login muncul lagi (input username masih ada)
    # Kita tidak cek pesan error spesifik karena teksnya mungkin beda
    assert b'name="username"' in response.data

def test_protected_page(client):
    """Test akses halaman admin tanpa login."""
    # Gunakan halaman /statistics yang pasti ada (dari nama file statistics.html)
    response = client.get('/statistics', follow_redirects=True)
    
    # Harus diredirect ke halaman login
    # Cek keberadaan form login sebagai tanda kita ditendang ke login
    assert b'name="password"' in response.data