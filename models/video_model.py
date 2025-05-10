from pydantic import BaseModel
from typing import List, Literal, Optional, Dict
import os
from datetime import datetime

class Transition(BaseModel):
    type: Literal["rotation", "rotation_inv", "zoom_in", "zoom_out", "translation", "translation_inv", "long_translation", "long_translation_inv"]
    duration: float

class SubtitleStyle(BaseModel):
    font: str
    size: int
    color: str
    background: str
    position: str

class Subtitle(BaseModel):
    enabled: bool
    style: SubtitleStyle

class VideoSettings(BaseModel):
    maxAudioSpeed: float
    resolution: str
    frameRate: int
    bitrate: str
    audioMismatchStrategy: Literal["extendDuration", "trimAudio", "speedUp"]

class Segment(BaseModel):
    index: int
    script: str
    image: str
    audio: str
    duration: float
    transition: Transition

class PlatformVideo(BaseModel):
    platform: Literal["youtube", "facebook", "tiktok"]
    video_id: str
    url: str
    upload_status: Literal["pending", "uploading", "success", "failed"] = "pending"
    upload_time: Optional[datetime] = None
    error_message: Optional[str] = None

class VideoModel(BaseModel):
    job_id: str
    user_id: str
    segments: List[Segment]
    subtitle: Subtitle
    videoSettings: VideoSettings
    backgroundMusic: Optional[str] = None
    
    # Generated fields
    output_video: str = None
    status: Literal["pending", "processing", "done", "failed"] = "pending"
    progress: int = 0
    log: str = ""
    duration: int = 0
    
    # Platform upload information
    platform_videos: Dict[str, PlatformVideo] = {}
    
    def __init__(self, **data):
        super().__init__(**data)
        # Tạo đường dẫn output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_video = f"output/video_{timestamp}.mp4"
        
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