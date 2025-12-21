# utils.py
import os
import shutil
from pathlib import Path
from fastapi import UploadFile

async def save_image_file(file: UploadFile, sub_folder: str = "images") -> str:
    """
    Resmi diske kaydeder ve veritabanı için yolunu döner.
    Örn: 'static/images/dosya.jpg' kaydeder, 'images/dosya.jpg' döner.
    """
    if not file or not file.filename:
        return None

    # Klasörü oluştur
    base_folder = f"static/{sub_folder}"
    os.makedirs(base_folder, exist_ok=True)
    
    # Dosya adını temizle
    safe_filename = file.filename.replace(" ", "_")
    
    # Çakışmayı önlemek için UUID veya timestamp eklenebilir ama şimdilik böyle kalsın
    file_path_on_disk = Path(base_folder) / safe_filename
    
    # Kaydet
    content = await file.read()
    with open(file_path_on_disk, "wb") as buffer:
        buffer.write(content)
        
    return f"{sub_folder}/{safe_filename}"