from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class YouTubeUploadRequest(BaseModel):
    userId: str = Field(..., description="ID của user cần upload video lên kênh YouTube")
    videoId: str = Field(..., description="ID của video cần upload")
    title: str = Field(..., description="Tiêu đề video")
    description: str = Field(..., description="Mô tả video")
    categoryId: str = Field("22", description="ID danh mục video (mặc định là '22' - People & Blogs)")
    privacyStatus: str = Field("private", description="Trạng thái riêng tư (private, unlisted, public)")
    tags: Optional[List[str]] = Field(None, description="Danh sách tags")

class YouTubeUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Tiêu đề mới")
    description: Optional[str] = Field(None, description="Mô tả mới")
    privacyStatus: Optional[str] = Field(None, description="Trạng thái riêng tư mới")
    tags: Optional[List[str]] = Field(None, description="Danh sách tags mới")

class YouTubeVideoResponse(BaseModel):
    videoId: str = Field(..., description="ID của video trên YouTube")
    title: str = Field(..., description="Tiêu đề video")
    description: str = Field(..., description="Mô tả video")
    privacyStatus: str = Field(..., description="Trạng thái riêng tư")
    url: str = Field(..., description="URL của video trên YouTube")

class PlatformVideo(BaseModel):
    platform: str
    video_id: str
    url: str
    upload_status: str
    upload_time: Optional[str] = None
    error_message: Optional[str] = None
    error_time: Optional[str] = None

class UserVideosResponse(BaseModel):
    userId: str
    videos: Dict[str, List[PlatformVideo]]  # Key là videoId, value là danh sách video trên các platform 