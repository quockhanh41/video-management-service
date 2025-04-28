from typing import Dict, Any
from pydantic import BaseModel
 
class VideoMessage(BaseModel):
    video_id: str
    data: Dict[str, Any] 