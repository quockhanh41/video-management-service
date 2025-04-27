import os
import sys
from pathlib import Path

# Lấy đường dẫn thư mục gốc của project
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from config.cloudinary import CloudinaryConfig
import json

def upload_assets():
    # Khởi tạo Cloudinary
    cloudinary = CloudinaryConfig()
    
    # Thư mục chứa assets
    test_dir = os.path.join(ROOT_DIR, "file_to_upload")
    
    # Upload ảnh
    image_urls = []
    for filename in os.listdir(test_dir):
        if filename.endswith(".png"):
            file_path = os.path.join(test_dir, filename)
            result = cloudinary.upload_file(file_path, folder="video_assets/images")
            image_urls.append(result["secure_url"])
            print(f"Đã upload ảnh: {filename}")
    
    # Upload audio
    audio_urls = []
    for filename in os.listdir(test_dir):
        if filename.endswith(".mp3"):
            file_path = os.path.join(test_dir, filename)
            result = cloudinary.upload_file(file_path, folder="video_assets/audios")
            audio_urls.append(result["secure_url"])
            print(f"Đã upload audio: {filename}")
    
    # Lưu URLs vào file JSON
    output_file = os.path.join(ROOT_DIR, "asset_urls.json")
    with open(output_file, "w") as f:
        json.dump({
            "images": image_urls,
            "audios": audio_urls
        }, f, indent=2)
    
    print(f"Đã lưu URLs vào file {output_file}")

if __name__ == "__main__":
    upload_assets() 