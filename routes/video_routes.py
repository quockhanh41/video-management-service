from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from controllers.video_controller import VideoController

router = APIRouter()
video_controller = VideoController()

class VideoGenerateRequest(BaseModel):
    scriptId: str
    scripts: List[str]
    images: List[str]
    audios: List[str]
    backgroundMusic: str = None
    subtitle: bool = False

class VideoGenerateResponse(BaseModel):
    message: str
    videoId: str

@router.post("/video/generate", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    try:
        # Chuyển đổi request thành dictionary và truyền vào controller
        data = request.model_dump()
        return await video_controller.generate_video(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 