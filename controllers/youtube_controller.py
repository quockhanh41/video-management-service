from service.youtube_service import YouTubeService
from service.video_service import VideoService
from models.youtube_model import (
    YouTubeUploadRequest, 
    YouTubeUpdateRequest, 
    YouTubeVideoResponse,
    UserVideosResponse,
    PlatformVideo
)
from typing import Dict, Any, Optional, List
import os
from pymongo import MongoClient
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
import logging
from datetime import datetime

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def get_youtube_tokens_from_db(user_id):
    #  connect to mongodb using URI from .env 
    client = MongoClient(os.getenv("BASE_MONGODB_URI"))
    db = client[os.getenv("MONGODB_DB", "auth")]
    user = db.users.find_one({"_id": user_id})
    if not user or not user.get("socialAccounts"):
        raise Exception("Không tìm thấy thông tin tài khoản YouTube của user")
    for acc in user["socialAccounts"]:
        if acc["platform"] == "youtube":
            return {
                "access_token": acc["accessToken"],
                "refresh_token": acc["refreshToken"],
            }
    raise Exception("User chưa liên kết tài khoản YouTube")

class YouTubeController:
    def __init__(self):
        self.video_service = VideoService()
        
    async def get_user_videos(self, user_id: str) -> UserVideosResponse:
        """
        Lấy danh sách video của user từ các platform
        Args:
            user_id: ID của user
        Returns:
            Danh sách video của user trên các platform
        """
        try:
            logger.info(f"Bắt đầu lấy danh sách video của user: {user_id}")
            
            # Lấy tất cả video của user từ database, điều kiện status là done
            videos = self.video_service.video_collection.find({"user_id": user_id, "status": "done"})
            
            # Tổ chức dữ liệu theo yêu cầu
            result = {
                "userId": user_id,
                "videos": []
            }
            
            for video in videos:
                video_info = {
                    "videoId": str(video["_id"]),
                    "outputPath": video.get("outputPath", ""),
                    "scriptId": video.get("script_id", ""),
                    "createdAt": video.get("createdAt", datetime.now()).isoformat(),
                    "duration": video.get("duration", 0),
                    "platform_videos": []
                }
                
                # Lấy thông tin video trên các platform
                platform_videos = video.get("platform_videos", {})
                if isinstance(platform_videos, dict):
                    for platform, platform_info in platform_videos.items():
                        if isinstance(platform_info, list):
                            for platform_video in platform_info:
                                if isinstance(platform_video, dict):
                                    video_info["platform_videos"].append({
                                        "platform": platform_video.get("platform", platform),
                                        "video_id": platform_video.get("video_id", ""),
                                        "url": platform_video.get("url", ""),
                                        "upload_status": platform_video.get("upload_status", ""),
                                        "upload_time": platform_video.get("upload_time"),
                                        "error_message": platform_video.get("error_message"),
                                        "error_time": platform_video.get("error_time")
                                    })
                
                result["videos"].append(video_info)
            
            logger.info(f"Đã lấy thành công danh sách video của user: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách video của user: {str(e)}")
            logger.error(f"Loại lỗi: {type(e).__name__}")
            raise Exception(f"Lỗi khi lấy danh sách video của user: {str(e)}")

    async def upload_video_from_form(
        self,
        file: UploadFile,
        title: str,
        description: str,
        privacy_status: str,
        tags: Optional[List[str]],
        youtube_service: YouTubeService
    ):
        """
        Upload video lên YouTube từ form data
        """
        try:
            logger.info(f"Bắt đầu xử lý upload video: {title}")
            logger.info(f"Privacy status: {privacy_status}")
            logger.info(f"Tags: {tags}")
            
            # Tạo thư mục temp nếu chưa tồn tại
            temp_dir = "temp"
            if not os.path.exists(temp_dir):
                logger.info(f"Tạo thư mục temp: {temp_dir}")
                os.makedirs(temp_dir)
            
            # Tạo tên file duy nhất
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file_path = os.path.join(temp_dir, f"{timestamp}_{file.filename}")
            
            logger.info(f"Đang lưu file tạm: {temp_file_path}")
            with open(temp_file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            try:
                logger.info("Bắt đầu upload lên YouTube...")
                result = await youtube_service.upload_video(
                    video_path=temp_file_path,
                    title=title,
                    description=description,
                    privacy_status=privacy_status,
                    tags=tags
                )
                logger.info(f"Upload thành công: {result}")
                return result
            finally:
                # Xóa file tạm
                logger.info(f"Xóa file tạm: {temp_file_path}")
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Lỗi chi tiết trong quá trình upload: {str(e)}")
            logger.error(f"Loại lỗi: {type(e).__name__}")
            if hasattr(e, 'resp'):
                logger.error(f"Response status: {e.resp.status}")
                logger.error(f"Response content: {e.content}")
            raise Exception(f"Lỗi khi upload video lên YouTube: {str(e)}")

    async def upload_video(self, data: YouTubeUploadRequest) -> YouTubeVideoResponse:
        """
        Upload video lên YouTube
        Args:
            data: Dữ liệu upload video
        Returns:
            Thông tin video đã upload
        """
        try:
            logger.info(f"Bắt đầu xử lý upload video: {data.title}")
            logger.info(f"Privacy status: {data.privacyStatus}")
            logger.info(f"Tags: {data.tags}")
            
            # Lấy thông tin video trực tiếp từ database
            video_info = await self.video_service.get_video_detail(data.videoId)
            if video_info["status"] != "done":
                raise Exception("Video chưa sẵn sàng để upload")
            # Lấy access token và refresh token từ DB
            tokens = get_youtube_tokens_from_db(data.userId)
            # Lấy client_id, client_secret, token_uri từ biến môi trường
            client_id = os.getenv("YOUTUBE_CLIENT_ID")
            client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
            token_uri = os.getenv("YOUTUBE_TOKEN_URI", "https://oauth2.googleapis.com/token")
            
            if not client_id or not client_secret:
                raise Exception("Thiếu thông tin xác thực YouTube (client_id hoặc client_secret)")
                
            # Khởi tạo YouTubeService với token
            youtube_service = YouTubeService(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                client_id=client_id,
                client_secret=client_secret,
                token_uri=token_uri
            )
           
            # Tải video từ Cloudinary về local
            video_url = video_info.get('originUrl') or video_info.get('url')
            if not video_url:
                raise Exception("Không tìm thấy URL của video")
                
            # Tạo thư mục temp nếu chưa tồn tại
            temp_dir = "temp"
            if not os.path.exists(temp_dir):
                logger.info(f"Tạo thư mục temp: {temp_dir}")
                os.makedirs(temp_dir)
                
            video_path = os.path.join(temp_dir, f"{data.videoId}.mp4")
            
            # Tải video từ Cloudinary
            download_result = os.system(f"curl -o {video_path} {video_url}")
            if download_result != 0:
                raise Exception("Không thể tải video từ Cloudinary")
                
            if not os.path.exists(video_path):
                raise Exception("Video không được tải về thành công")
            
            # Upload lên YouTube
            logger.info("Bắt đầu upload lên YouTube...")
            result = await youtube_service.upload_video(
                video_path=video_path,
                title=data.title,
                description=data.description,
                category_id=data.categoryId,
                privacy_status=data.privacyStatus,
                tags=data.tags
            )
            logger.info(f"Upload thành công: {result}")
            
            # Cập nhật thông tin video lên YouTube vào VideoModel
            self.video_service.video_collection.update_one(
                {"_id": ObjectId(data.videoId)},
                {
                    "$push": {
                        "platform_videos.youtube": {
                            "platform": "youtube",
                            "video_id": result.get("videoId", ""),
                            "url": result.get("url", ""),
                            "upload_status": "success",
                            "upload_time": datetime.now().isoformat()
                        }
                    }
                }
            )
            
            # Xóa file tạm
            logger.info(f"Xóa file tạm: {video_path}")
            if os.path.exists(video_path):
                os.remove(video_path)
            return YouTubeVideoResponse(**result)
        except Exception as e:
            # Cập nhật trạng thái lỗi vào VideoModel nếu upload thất bại
            if "data.videoId" in locals():
                try:
                    self.video_service.video_collection.update_one(
                        {"_id": ObjectId(data.videoId)},
                        {
                            "$set": {
                                "platform_videos.youtube": {
                                    "platform": "youtube",
                                    "video_id": "",
                                    "url": "",
                                    "upload_status": "failed",
                                    "error_message": str(e),
                                    "error_time": datetime.now().isoformat()
                                }
                            }
                        }
                    )
                except Exception as db_error:
                    logger.error(f"Lỗi khi cập nhật trạng thái lỗi vào database: {str(db_error)}")
            
            logger.error(f"Lỗi chi tiết trong quá trình upload: {str(e)}")
            logger.error(f"Loại lỗi: {type(e).__name__}")
            if hasattr(e, 'resp'):
                logger.error(f"Response status: {e.resp.status}")
                logger.error(f"Response content: {e.content}")
            raise Exception(f"Lỗi khi upload video lên YouTube: {str(e)}")

    async def update_video(self, youtube_video_id: str, data: YouTubeUpdateRequest) -> YouTubeVideoResponse:
        try:
            # Lấy client_id, client_secret, token_uri từ biến môi trường (nếu cần cập nhật logic cho từng user, có thể truyền vào tương tự upload)
            client_id = os.getenv("YOUTUBE_CLIENT_ID")
            client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
            token_uri = os.getenv("YOUTUBE_TOKEN_URI", "https://oauth2.googleapis.com/token")
            # Ở đây bạn cần truyền access_token/refresh_token nếu muốn update theo từng user
            youtube_service = YouTubeService(client_id=client_id, client_secret=client_secret, token_uri=token_uri)
            result = await youtube_service.update_video(
                video_id=youtube_video_id,
                title=data.title,
                description=data.description,
                privacy_status=data.privacyStatus,
                tags=data.tags
            )
            return YouTubeVideoResponse(**result)
        except Exception as e:
            raise Exception(f"Lỗi khi cập nhật video trên YouTube: {str(e)}")

    async def delete_video(self, youtube_video_id: str) -> bool:
        try:
            client_id = os.getenv("YOUTUBE_CLIENT_ID")
            client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
            token_uri = os.getenv("YOUTUBE_TOKEN_URI", "https://oauth2.googleapis.com/token")
            youtube_service = YouTubeService(client_id=client_id, client_secret=client_secret, token_uri=token_uri)
            return await youtube_service.delete_video(youtube_video_id)
        except Exception as e:
            raise Exception(f"Lỗi khi xóa video trên YouTube: {str(e)}")

def get_youtube_service() -> YouTubeService:
    try:
        logger.info("Đang khởi tạo YouTubeService...")
        service = YouTubeService(
            access_token=os.getenv('YOUTUBE_ACCESS_TOKEN'),
            refresh_token=os.getenv('YOUTUBE_REFRESH_TOKEN'),
            client_id=os.getenv('YOUTUBE_CLIENT_ID'),
            client_secret=os.getenv('YOUTUBE_CLIENT_SECRET'),
            token_uri=os.getenv('YOUTUBE_TOKEN_URI')
        )
        logger.info("Đã khởi tạo YouTubeService thành công")
        return service
    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo YouTubeService: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi khởi tạo YouTubeService: {str(e)}")

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...),
    privacy_status: str = Form("private"),
    tags: Optional[List[str]] = Form(None),
    youtube_service: YouTubeService = Depends(get_youtube_service)
):
    try:
        logger.info(f"Bắt đầu xử lý upload video: {title}")
        logger.info(f"Privacy status: {privacy_status}")
        logger.info(f"Tags: {tags}")
        
        # Tạo thư mục temp nếu chưa tồn tại
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            logger.info(f"Tạo thư mục temp: {temp_dir}")
            os.makedirs(temp_dir)
        
        # Tạo tên file duy nhất
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file_path = os.path.join(temp_dir, f"{timestamp}_{file.filename}")
        
        logger.info(f"Đang lưu file tạm: {temp_file_path}")
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            logger.info("Bắt đầu upload lên YouTube...")
            result = await youtube_service.upload_video(
                video_path=temp_file_path,
                title=title,
                description=description,
                privacy_status=privacy_status,
                tags=tags
            )
            logger.info(f"Upload thành công: {result}")
            return result
        finally:
            # Xóa file tạm
            logger.info(f"Xóa file tạm: {temp_file_path}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f"Lỗi chi tiết trong quá trình upload: {str(e)}")
        logger.error(f"Loại lỗi: {type(e).__name__}")
        if hasattr(e, 'resp'):
            logger.error(f"Response status: {e.resp.status}")
            logger.error(f"Response content: {e.content}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi upload video lên YouTube: {str(e)}")
 