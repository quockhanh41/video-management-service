from pydantic import BaseModel
from typing import Dict, Any

class VideoMessage(BaseModel):
    video_id: str
    data: Dict[str, Any] 