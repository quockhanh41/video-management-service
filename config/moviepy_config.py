from moviepy.config import change_settings
import os
from pathlib import Path

# Lấy đường dẫn thư mục gốc của project
ROOT_DIR = Path(__file__).parent.parent

# Cấu hình đường dẫn ImageMagick dựa vào môi trường
NODE_ENV = os.getenv("NODE_ENV", "development")

if NODE_ENV == "production":
    # Trong môi trường production (Railway), sử dụng đường dẫn mặc định
    IMAGEMAGICK_PATH = "/usr/bin/convert"
else:
    # Trong môi trường development, sử dụng đường dẫn local trong thư mục bin
    IMAGEMAGICK_PATH = os.path.join(ROOT_DIR, "bin", "ImageMagick", "magick.exe")

print(f"Using ImageMagick path: {IMAGEMAGICK_PATH}")

change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

# Cấu hình thư mục temp
TEMP_DIR = os.path.join(ROOT_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
change_settings({"TEMP_DIR": TEMP_DIR}) 

