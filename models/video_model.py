from pydantic import BaseModel
from typing import List, Literal, Optional, Dict
import os
from datetime import datetime

class Segment(BaseModel):
    index: int
    script: str
    image: str
    audio: str
    duration: float

class PlatformVideo(BaseModel):
    platform: Literal["youtube", "facebook", "tiktok"]
    video_id: str
    url: str
    upload_status: Literal["pending", "uploading", "success", "failed"] = "pending"
    upload_time: Optional[datetime] = None
    error_message: Optional[str] = None

class VideoModel(BaseModel):
    # Input fields
    job_id: str
    script_id: str
    user_id: str
    segments: List[Segment]
    backgroundMusic: Optional[str] = None
    
    # Video settings
    resolution: str = "1080"  # Độ phân giải mặc định là 1080p
    aspectRatio: str = "16:9"  # Tỷ lệ khung hình mặc định là 16:9
    
    # Generated fields
    status: Literal["pending", "processing", "done", "failed"] = "pending"
    progress: int = 0
    log: str = ""
    duration: int = 0
    render_id: Optional[str] = None
    outputPath: Optional[str] = None
    
    # Platform upload information
    platform_videos: Dict[str, PlatformVideo] = {}
    
    def __init__(self, **data):
        super().__init__(**data)
        # Tạo đường dẫn output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.outputPath = f"output/video_{timestamp}.mp4"
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs("output", exist_ok=True)
        
    def add_platform_video(self, platform: str, video_id: str, url: str):
        """Thêm thông tin video đã upload lên platform"""
        self.platform_videos[platform] = PlatformVideo(
            platform=platform,
            video_id=video_id,
            url=url
        )
        
    def update_platform_status(self, platform: str, status: str, error_message: Optional[str] = None):
        """Cập nhật trạng thái upload lên platform"""
        if platform in self.platform_videos:
            self.platform_videos[platform].upload_status = status
            self.platform_videos[platform].error_message = error_message
            if status == "success":
                self.platform_videos[platform].upload_time = datetime.now()