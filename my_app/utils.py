import os
from PIL import Image

def compress_image(file_storage, save_path, quality=60, max_size=(1024, 1024)):
    """
    Mengkompres gambar, resize jika terlalu besar, dan konversi ke JPEG.
    
    :param file_storage: Object file dari request.files
    :param save_path: Path lengkap lokasi penyimpanan
    :param quality: Kualitas output JPEG (1-100), default 60 (sudah cukup bagus utk web)
    :param max_size: Tuple (width, height) maksimal. Gambar akan di-resize proporsional.
    """
    try:
        # Buka gambar menggunakan Pillow
        image = Image.open(file_storage)
        
        # Konversi ke RGB (Penting jika inputnya PNG transparan atau RGBA)
        # Kita ubah semua jadi JPEG agar seragam dan kompresi maksimal
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        # Resize jika dimensi melebihi batas (misal dari 4000x3000 jadi max 1024px)
        # Ini sangat menghemat bandwidth
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Simpan dengan optimasi
        # optimize=True akan melakukan pass tambahan untuk mengecilkan size
        image.save(save_path, format='JPEG', quality=quality, optimize=True)
        
        return True
    except Exception as e:
        print(f"Gagal mengkompres gambar: {e}")
        return False