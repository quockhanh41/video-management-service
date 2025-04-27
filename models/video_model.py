from pydantic import BaseModel
from typing import List, Literal
import os
from datetime import datetime

class VideoModel(BaseModel):
    script_id: str
    scripts: List[str]
    images: List[str]
    audios: List[str]
    subtitle: bool = False
    backgroundMusic: str = None
    
    # Generated fields
    output_video: str = None
    status: Literal["pending", "processing", "done", "failed"] = "pending"
    progress: int = 0
    log: str = ""
    
    def __init__(self, **data):
        super().__init__(**data)
        # Tạo đường dẫn output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_video = f"output/video_{timestamp}.mp4"
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs("output", exist_ok=True)