from moviepy.config import change_settings
import os
from pathlib import Path

# Lấy đường dẫn thư mục gốc của project
ROOT_DIR = Path(__file__).parent.parent

# Cấu hình đường dẫn ImageMagick
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe"
# IMAGEMAGICK_PATH = os.path.join(ROOT_DIR, "bin", "ImageMagick", "magick.exe")

change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

# Cấu hình thư mục temp
TEMP_DIR = os.path.join(ROOT_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
change_settings({"TEMP_DIR": TEMP_DIR}) 

