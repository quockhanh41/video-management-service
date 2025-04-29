from pydantic import BaseModel
from typing import List, Literal, Optional
import os
from datetime import datetime

class Transition(BaseModel):
    type: Literal["fade", "slide", "zoom", "wipe", "dissolve", "fade_to_black"]
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

class VideoModel(BaseModel):
    scriptId: str
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
    
    def __init__(self, **data):
        super().__init__(**data)
        # Tạo đường dẫn output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_video = f"output/video_{timestamp}.mp4"
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs("output", exist_ok=True)