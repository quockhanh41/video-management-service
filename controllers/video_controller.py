from service.video_service import VideoService
from service.message_service import MessageService
from typing import Dict, Any
from models.video_model import VideoModel
import requests
import os
from datetime import datetime
from bson import ObjectId

class VideoController:
    def __init__(self):
        self.video_service = VideoService()
        self.message_service = MessageService()
    
    async def generate_video(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Gọi service để xử lý logic tạo video
        Args:
            data: Dữ liệu đầu vào
        Returns:
            Dict chứa message và videoId
        """
        # Tạo video và lấy video_id
        result = await self.video_service.generate_video(data)
        
        # Gửi message vào queue
        self.message_service.publish_message({
            "video_id": result["videoId"],
            "data": data
        })
        
        return result

    @staticmethod
    def _validate_inputs(data: Dict[str, Any]) -> bool:
        """
        Kiểm tra tính hợp lệ của các input
        """
        # Kiểm tra số lượng scripts, images và audios phải bằng nhau
        if len(data["scripts"]) != len(data["images"]) or \
           len(data["scripts"]) != len(data["audios"]):
            raise ValueError("Số lượng scripts, images và audios phải bằng nhau")
        
        # Kiểm tra các link images và audios
        for image_url in data["images"]:
            try:
                response = requests.head(image_url)
                if response.status_code != 200:
                    raise ValueError(f"Link ảnh không hợp lệ: {image_url}")
            except:
                raise ValueError(f"Không thể truy cập link ảnh: {image_url}")
                
        for audio_url in data["audios"]:
            try:
                response = requests.head(audio_url)
                if response.status_code != 200:
                    raise ValueError(f"Link audio không hợp lệ: {audio_url}")
            except:
                raise ValueError(f"Không thể truy cập link audio: {audio_url}")
            
        return True

    @staticmethod
    def _create_video(video_model: VideoModel) -> str:
        """
        Tạo video từ model
        """
        try:
            # TODO: Implement video creation logic
            # 1. Download images and audios
            # 2. Generate video for each script-image-audio combination
            # 3. Combine all videos
            # 4. Add background music if needed
            # 5. Export final video
            
            # Tạm thời trả về ID ngẫu nhiên
            return f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        except Exception as e:
            raise Exception(f"Lỗi khi tạo video: {str(e)}")

    @staticmethod
    def _cleanup(video_model: VideoModel):
        """
        Dọn dẹp các file tạm
        """
        try:
            if os.path.exists(video_model.temp_video):
                os.remove(video_model.temp_video)
        except Exception as e:
            print(f"Lỗi khi dọn dẹp file tạm: {str(e)}") 