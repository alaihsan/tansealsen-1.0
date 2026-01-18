import shutil
import os
import sys

def remove_folder(folder_name):
    """
    Menghapus folder beserta isinya jika folder tersebut ada.
    """
    current_dir = os.getcwd()
    folder_path = os.path.join(current_dir, folder_name)

    if os.path.exists(folder_path):
        try:
            print(f"Sedang menghapus folder: {folder_path} ...")
            # shutil.rmtree digunakan untuk menghapus folder dan seluruh isinya
            shutil.rmtree(folder_path)
            print(f"Berhasil: '{folder_name}' telah dihapus.")
        except Exception as e:
            print(f"Gagal menghapus '{folder_name}'. Error: {e}")
    else:
        print(f"Info: Folder '{folder_name}' tidak ditemukan di direktori ini.")

def main():
    # Daftar folder yang ingin dihapus demi keamanan dan kebersihan repository
    folders_to_delete = ['.idea', '.venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.env']
    
    print("--- MULAI PEMBERSIHAN PROJECT ---")
    print(f"Lokasi saat ini: {os.getcwd()}")
    
    confirmation = input("Apakah kamu yakin ingin menghapus folder konfigurasi & venv? (y/n): ")
    
    if confirmation.lower() == 'y':
        for folder in folders_to_delete:
            remove_folder(folder)
        print("\n--- SELESAI ---")
        print("Silakan buat virtual environment baru jika diperlukan (python -m venv .venv)")
    else:
        print("Operasi dibatalkan.")

if __name__ == "__main__":
    main()