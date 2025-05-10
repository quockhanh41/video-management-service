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
        # Kiểm tra các trường bắt buộc
        required_fields = ["job_id", "segments", "subtitle", "videoSettings"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Thiếu trường bắt buộc: {field}")
        
        # Kiểm tra segments
        if not isinstance(data["segments"], list) or len(data["segments"]) == 0:
            raise ValueError("Segments phải là một mảng không rỗng")
        
        # Kiểm tra từng segment
        for i, segment in enumerate(data["segments"]):
            # Kiểm tra các trường bắt buộc của segment
            segment_fields = ["index", "script", "image", "audio", "duration", "transition"]
            for field in segment_fields:
                if field not in segment:
                    raise ValueError(f"Segment {i} thiếu trường bắt buộc: {field}")
            
            # Kiểm tra transition
            if not isinstance(segment["transition"], dict):
                raise ValueError(f"Transition của segment {i} phải là một object")
            
            transition_fields = ["type", "duration"]
            for field in transition_fields:
                if field not in segment["transition"]:
                    raise ValueError(f"Transition của segment {i} thiếu trường bắt buộc: {field}")
            
            if segment["transition"]["type"] not in ["fade", "slide"]:
                raise ValueError(f"Transition type của segment {i} phải là 'fade' hoặc 'slide'")
            
            if not isinstance(segment["transition"]["duration"], (int, float)) or segment["transition"]["duration"] <= 0:
                raise ValueError(f"Transition duration của segment {i} phải là số dương")
        
        # Kiểm tra subtitle
        if not isinstance(data["subtitle"], dict):
            raise ValueError("Subtitle phải là một object")
        
        subtitle_fields = ["enabled", "style"]
        for field in subtitle_fields:
            if field not in data["subtitle"]:
                raise ValueError(f"Subtitle thiếu trường bắt buộc: {field}")
        
        # Kiểm tra subtitle style
        if not isinstance(data["subtitle"]["style"], dict):
            raise ValueError("Subtitle style phải là một object")
        
        style_fields = ["font", "size", "color", "background", "position"]
        for field in style_fields:
            if field not in data["subtitle"]["style"]:
                raise ValueError(f"Subtitle style thiếu trường bắt buộc: {field}")
        
        if data["subtitle"]["style"]["position"] not in ["bottom", "center"]:
            raise ValueError("Subtitle position phải là 'bottom' hoặc 'center'")
        
        # Kiểm tra video settings
        if not isinstance(data["videoSettings"], dict):
            raise ValueError("Video settings phải là một object")
        
        settings_fields = ["maxAudioSpeed", "resolution", "frameRate", "bitrate", "audioMismatchStrategy"]
        for field in settings_fields:
            if field not in data["videoSettings"]:
                raise ValueError(f"Video settings thiếu trường bắt buộc: {field}")
        
        if data["videoSettings"]["audioMismatchStrategy"] not in ["extendDuration", "trimAudio", "speedUp"]:
            raise ValueError("Audio mismatch strategy phải là 'extendDuration', 'trimAudio' hoặc 'speedUp'")
        
        # Kiểm tra các link images và audios
        for segment in data["segments"]:
            try:
                response = requests.head(segment["image"])
                if response.status_code != 200:
                    raise ValueError(f"Link ảnh không hợp lệ: {segment['image']}")
            except:
                raise ValueError(f"Không thể truy cập link ảnh: {segment['image']}")
                
            try:
                response = requests.head(segment["audio"])
                if response.status_code != 200:
                    raise ValueError(f"Link audio không hợp lệ: {segment['audio']}")
            except:
                raise ValueError(f"Không thể truy cập link audio: {segment['audio']}")
        
        # Kiểm tra background music nếu có
        if "backgroundMusic" in data and data["backgroundMusic"]:
            try:
                response = requests.head(data["backgroundMusic"])
                if response.status_code != 200:
                    raise ValueError(f"Link nhạc nền không hợp lệ: {data['backgroundMusic']}")
            except:
                raise ValueError(f"Không thể truy cập link nhạc nền: {data['backgroundMusic']}")
            
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

    async def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Lấy trạng thái xử lý của video
        Args:
            video_id: ID của video cần kiểm tra
        Returns:
            Dict chứa thông tin trạng thái video
        """
        try:
            # Lấy thông tin trạng thái từ service
            status_info = await self.video_service.get_video_status(video_id)
            
            return {
                "videoId": video_id,
                "status": status_info.get("status", "unknown"),
                "progress": status_info.get("progress", 0),
                "log": status_info.get("log", "Không có thông tin")
            }
        except Exception as e:
            raise Exception(f"Lỗi khi lấy trạng thái video: {str(e)}")

    async def get_video_detail(self, video_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết của video
        Args:
            video_id: ID của video cần lấy thông tin
        Returns:
            Dict chứa thông tin chi tiết video
        """
        try:
            # Lấy thông tin chi tiết từ service
            video_info = await self.video_service.get_video_detail(video_id)
            
            return {
                "videoId": video_id,
                "job_id": video_info.get("job_id", ""),
                "url": video_info.get("outputPath", ""),
                "status": video_info.get("status", "unknown"),
                "duration": video_info.get("duration", 0),
                "createdAt": video_info.get("createdAt", datetime.now())
            }
        except Exception as e:
            raise Exception(f"Lỗi khi lấy thông tin video: {str(e)}")

    async def get_video_preview(self, video_id: str) -> Dict[str, str]:
        """
        Lấy URL stream xem trước video
        Args:
            video_id: ID của video cần xem trước
        Returns:
            Dict chứa URL stream, cloud_name và public_id
        """
        try:
            # Lấy thông tin video từ service
            video_info = await self.video_service.get_video_preview(video_id)
            
            return {
                "streamUrl": video_info.get("streamUrl", ""),
                "cloudName": video_info.get("cloudName", ""),
                "publicId": video_info.get("publicId", "")
            }
        except Exception as e:
            raise Exception(f"Lỗi khi lấy URL stream: {str(e)}") 