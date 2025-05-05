from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Literal, Optional
from bson import ObjectId
from controllers.video_controller import VideoController
from datetime import datetime

router = APIRouter()
video_controller = VideoController()

class Transition(BaseModel):
    type: Literal["rotation", "rotation_inv", "zoom_in", "zoom_out", "translation", "translation_inv", "long_translation", "long_translation_inv"]
    duration: float

class SubtitleStyle(BaseModel):
    font: str
    size: int
    color: str
    background: str
    position: Literal["bottom", "center"]

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

class VideoGenerateRequest(BaseModel):
    scriptId: str
    segments: List[Segment]
    subtitle: Subtitle
    videoSettings: VideoSettings
    backgroundMusic: Optional[str] = None

class VideoGenerateResponse(BaseModel):
    message: str
    videoId: str

class VideoStatusResponse(BaseModel):
    videoId: str
    status: str
    progress: int
    log: str

class VideoDetailResponse(BaseModel):
    videoId: str
    scriptId: str
    url: str
    status: str
    duration: int
    createdAt: datetime

class VideoPreviewResponse(BaseModel):
    streamUrl: str
    cloudName: str
    publicId: str

@router.post("/video/generate", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    try:
        # Chuyển đổi request thành dictionary và truyền vào controller
        data = request.model_dump()
        return await video_controller.generate_video(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/video/status/{videoId}", response_model=VideoStatusResponse)
async def get_video_status(videoId: str):
    try:
        return await video_controller.get_video_status(videoId)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/video/{videoId}", response_model=VideoDetailResponse)
async def get_video_detail(videoId: str):
    try:
        return await video_controller.get_video_detail(videoId)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/video/preview/{videoId}", response_model=VideoPreviewResponse)
async def get_video_preview(videoId: str):
    try:
        return await video_controller.get_video_preview(videoId)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 