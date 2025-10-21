# tansealsen-1.0
Tentu, berikut adalah draf untuk file `README.md` yang menjelaskan aplikasi Anda dan cara setup-nya.

-----

# Tanse App - Aplikasi Pencatatan Pelanggaran Murid

Tanse App adalah aplikasi web sederhana yang dibangun menggunakan Flask untuk membantu guru dan staf sekolah dalam mencatat dan mengelola data pelanggaran murid. Aplikasi ini memungkinkan pencatatan yang terstruktur, lengkap dengan bukti foto dan riwayat per murid.

Aplikasi ini dibuat oleh Tim IT Alsen 22.

## Fitur Utama

  * **Sistem Login:** Melindungi aplikasi dengan halaman login sederhana.
  * **CRUD Pelanggaran:** Menambah, Melihat, dan Menghapus data pelanggaran.
  * **Upload Bukti:** Mengunggah bukti pelanggaran berupa gambar (PNG, JPG, JPEG, GIF).
  * **Riwayat Murid:** Melihat seluruh riwayat pelanggaran untuk murid tertentu (fitur yang baru ditambahkan).
  * **Pencarian & Filter:** Mencari murid berdasarkan nama atau kelas langsung di halaman utama.
  * **Paginasi:** Daftar pelanggaran ditampilkan dalam beberapa halaman (10 item per halaman) agar rapi.
  * **Database Otomatis:** Menggunakan SQLite (`site.db`) yang akan dibuat secara otomatis saat aplikasi pertama kali dijalankan.

## Setup dan Instalasi

Berikut adalah langkah-langkah untuk menjalankan aplikasi ini di komputer lokal Anda.

### 1\. Persiapan Awal

1.  Pastikan Anda memiliki **Python 3** terinstal di sistem Anda.
2.  Buka terminal atau command prompt.
3.  Pindah (navigasi) ke folder root proyek ini (folder `tansealsen-1.0`).

### 2\. Buat dan Aktifkan Virtual Environment

Sangat disarankan untuk menggunakan *virtual environment* (vEnv) agar dependensi proyek tidak tercampur.

```bash
# 1. Buat vEnv (cukup sekali)
python -m venv .venv

# 2. Aktifkan vEnv (lakukan setiap kali Anda ingin menjalankan proyek)

# Jika Anda menggunakan PowerShell (Windows)
.\.venv\Scripts\Activate.ps1
```

*(Catatan: Jika Anda menggunakan Git Bash atau terminal lain, perintahnya mungkin `source .venv/Scripts/activate`)*

### 3\. Install Dependensi

Setelah vEnv aktif, install library Python yang diperlukan (`Flask` dan `Flask-SQLAlchemy`).

```bash
pip install Flask Flask-SQLAlchemy
```

## Cara Menjalankan Aplikasi

1.  Pastikan *virtual environment* Anda sudah aktif (ditandai dengan `(.venv)` di awal baris terminal).
2.  Pindah ke direktori aplikasi:
    ```bash
    cd my_app
    ```
3.  Jalankan file `app.py` menggunakan Python:
    ```bash
    python app.py
    ```
4.  Aplikasi akan berjalan dalam mode debug. Buka browser Anda dan akses alamat:
    **`http://127.0.0.1:5000/`**

## Kredensial Login

Aplikasi ini menggunakan kredensial login *hardcode*.

  * **Username:** `admin`
  * **Password:** `admin`
