from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from controllers.youtube_controller import YouTubeController, get_youtube_service
from models.youtube_model import (
    YouTubeUploadRequest, 
    YouTubeUpdateRequest, 
    YouTubeVideoResponse,
    UserVideosResponse
)
from typing import Dict, Optional, List
from service.youtube_service import YouTubeService

router = APIRouter()
youtube_controller = YouTubeController()

@router.get("/user/{user_id}/videos", response_model=UserVideosResponse)
async def get_user_videos(user_id: str):
    """
    Lấy danh sách video của user từ các platform
    Args:
        user_id: ID của user
    Returns:
        Danh sách video của user trên các platform
    """
    try:
        return await youtube_controller.get_user_videos(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...),
    privacy_status: str = Form("private"),
    tags: Optional[List[str]] = Form(None),
    youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """
    Upload video lên YouTube thông qua form data
    """
    try:
        return await youtube_controller.upload_video_from_form(
            file=file,
            title=title,
            description=description,
            privacy_status=privacy_status,
            tags=tags,
            youtube_service=youtube_service
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/youtube/upload", response_model=YouTubeVideoResponse)
async def upload_video(data: YouTubeUploadRequest):
    """
    Upload video lên YouTube
    """
    try:
        return await youtube_controller.upload_video(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/youtube/{youtube_video_id}", response_model=YouTubeVideoResponse)
async def update_video(youtube_video_id: str, data: YouTubeUpdateRequest):
    """
    Cập nhật thông tin video trên YouTube
    """
    try:
        return await youtube_controller.update_video(youtube_video_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/youtube/{youtube_video_id}")
async def delete_video(youtube_video_id: str) -> Dict[str, bool]:
    """
    Xóa video trên YouTube
    """
    try:
        result = await youtube_controller.delete_video(youtube_video_id)
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 