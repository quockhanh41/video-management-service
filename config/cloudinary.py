import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
import os

load_dotenv()

class CloudinaryConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CloudinaryConfig, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET")
        )
    
    def upload_file(self, file_path: str, folder: str = "video_assets", eager_transformations: list = None, resource_type: str = "auto") -> dict:
        """
        Upload file lên Cloudinary
        Args:
            file_path: Đường dẫn file cần upload
            folder: Thư mục trên Cloudinary
            eager_transformations: Danh sách các transformation cần tạo trước
            resource_type: Loại resource (auto, image, video, raw)
        Returns:
            Dict chứa thông tin file đã upload
        """
        try:
            result = cloudinary.uploader.upload(
                file_path,
                folder=folder,
                resource_type=resource_type,
                eager_async=True,
                eager=eager_transformations,
                eager_notification_url=os.getenv("CLOUDINARY_NOTIFICATION_URL", None)
            )
            return result
        except Exception as e:
            raise Exception(f"Lỗi khi upload file lên Cloudinary: {str(e)}") 