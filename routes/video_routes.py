from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Literal, Optional
from bson import ObjectId
from controllers.video_controller import VideoController
from datetime import datetime
import requests
import json
import os
from dotenv import load_dotenv
import time
from service.video_service import VideoService
from service.shotstack_service import ShotstackService
from models.video_model import VideoModel

router = APIRouter()
video_controller = VideoController()

# Load environment variables
load_dotenv()

# Shotstack API configuration
API_KEY = os.getenv("SHOTSTACK_API_KEY")
ENVIRONMENT = os.getenv("SHOTSTACK_ENVIRONMENT", "PRODUCTION")
API_URL = "https://api.shotstack.io/v1/render" if ENVIRONMENT == "PRODUCTION" else "https://api.sandbox.shotstack.io/v1/render"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

class Subtitle(BaseModel):
    enabled: bool = False

class Segment(BaseModel):
    index: int
    script: str
    image: str
    audio: str
    duration: float

class VideoGenerateRequest(BaseModel):
    job_id: str
    script_id: str
    user_id: str
    segments: List[Segment]
    backgroundMusic: Optional[str] = None
    resolution: str = "1080"
    aspectRatio: str = "16:9"
    subtitle: Subtitle = Subtitle()

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
    job_id: str
    script_id: str
    url: str
    streamUrl: str
    status: str
    duration: int
    createdAt: datetime

class VideoPreviewResponse(BaseModel):
    url: str
    streamUrl: str

def submit_render(timeline_data):
    """
    Gửi request render video đến Shotstack API
    """
    try:
        response = requests.post(API_URL, headers=HEADERS, json=timeline_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500

def get_render_status(render_id):
    """
    Kiểm tra trạng thái render của video
    """
    try:
        response = requests.get(
            f"{API_URL}/{render_id}",
            headers=HEADERS
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500

@router.post("/video/generate", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """
    Route tạo video mới sử dụng Shotstack API
    """
    try:
        data = request.model_dump()
        return await video_controller.generate_video(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/video/status/{videoId}", response_model=VideoStatusResponse)
async def get_video_status(videoId: str):
    """
    Route kiểm tra trạng thái của video
    """
    try:
        return await video_controller.get_video_status(videoId)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/video/preview/{videoId}", response_model=VideoPreviewResponse)
async def get_video_preview(videoId: str):
    """
    Route lấy URL xem trước video
    """
    try:
        return await video_controller.get_video_preview(videoId)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/video/details/{videoId}", response_model=VideoDetailResponse)
async def get_video_detail(videoId: str):
    """
    Route lấy thông tin chi tiết của video
    """
    try:
        return await video_controller.get_video_detail(videoId)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 