from models.video_model import VideoModel
from typing import Dict, Any, List
import os
from datetime import datetime
from bson import ObjectId
from config.mongodb import MongoDB
from service.shotstack_service import ShotstackService
import asyncio
import time

class VideoService:
    def __init__(self):
        self.mongodb = MongoDB()
        self.video_collection = self.mongodb.get_collection("videos")
        self.shotstack = ShotstackService()
    
    async def generate_video(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Xử lý toàn bộ logic tạo video
        Args:
            data: Dữ liệu đầu vào
        Returns:
            Dict chứa message và videoId
        """
        try:
            # Validate ObjectId
            ObjectId(data["job_id"])
            
            # Validate inputs
            self._validate_inputs(data)
            
            # Tạo model
            video_model = VideoModel(
                job_id=data["job_id"],
                script_id=data["script_id"],
                user_id=data["user_id"],
                segments=data["segments"],
                backgroundMusic=data.get("backgroundMusic"),
                status="pending",
                progress=0,
                log="Đang chờ xử lý..."
            )
            
            # Lưu thông tin video vào MongoDB
            video_data = {
                "job_id": data["job_id"],
                "script_id": data["script_id"],
                "user_id": data["user_id"],
                "segments": data["segments"],
                "backgroundMusic": data.get("backgroundMusic"),
                "status": video_model.status,
                "progress": video_model.progress,
                "log": video_model.log,
                "createdAt": datetime.now()
            }
            result = self.video_collection.insert_one(video_data)
            video_id = str(result.inserted_id)
            
            # Tạo timeline và gửi request render
            timeline = self.shotstack.create_timeline(
                data["segments"],
                data.get("backgroundMusic"),
                data.get("subtitle", {}).get("enabled", False),
                data.get("resolution", "1080"),
                data.get("aspectRatio", "16:9")
            )
            print(timeline)
            render_response = self.shotstack.submit_render(timeline)
            
            if not render_response or "response" not in render_response or "id" not in render_response["response"]:
                raise Exception("Không thể lấy Render ID từ response")
                
            render_id = render_response["response"]["id"]
            
            # Cập nhật render_id vào database
            self.video_collection.update_one(
                {"_id": ObjectId(video_id)},
                {
                    "$set": {
                        "render_id": render_id,
                        "status": "processing",
                        "log": "Đang render video..."
                    }
                }
            )
            
            # Bắt đầu kiểm tra trạng thái render
            asyncio.create_task(self.check_render_status(video_id, render_id))
            
            return {
                "message": "Đang tiến hành tạo video...",
                "videoId": video_id
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi tạo video: {str(e)}")

    async def check_render_status(self, video_id: str, render_id: str):
        """
        Kiểm tra trạng thái render của video
        """
        max_attempts = 60  # Số lần kiểm tra tối đa
        interval = 5  # Thời gian giữa các lần kiểm tra (giây)
        
        for attempt in range(max_attempts):
            try:
                # Kiểm tra trạng thái render
                render_status = self.shotstack.get_render_status(render_id)
                
                if not render_status:
                    continue
                    
                status = render_status.get("response", {}).get("status")
                
                if status == "done":
                    # Lấy URL video từ response
                    video_url = render_status["response"]["url"]
                    
                    # Lấy thông tin video từ database để tính duration
                    video = self.video_collection.find_one({"_id": ObjectId(video_id)})
                    if not video:
                        raise ValueError(f"Không tìm thấy video với ID: {video_id}")
                        
                    # Tính tổng duration từ các segments
                    total_duration = sum(segment.get("duration", 0) for segment in video.get("segments", []))
                    
                    # Cập nhật trạng thái, URL video và duration
                    self.video_collection.update_one(
                        {"_id": ObjectId(video_id)},
                        {
                            "$set": {
                                "status": "done",
                                "outputPath": video_url,
                                "progress": 100,
                                "log": "Hoàn thành!",
                                "duration": total_duration
                            }
                        }
                    )
                    return
                    
                elif status == "failed":
                    error_message = render_status.get("response", {}).get("error", "Không xác định")
                    self.video_collection.update_one(
                        {"_id": ObjectId(video_id)},
                        {
                            "$set": {
                                "status": "failed",
                                "log": f"Lỗi render: {error_message}"
                            }
                        }
                    )
                    return
                    
                # Cập nhật tiến độ
                progress = render_status.get("response", {}).get("progress", 0)
                self.video_collection.update_one(
                    {"_id": ObjectId(video_id)},
                    {
                        "$set": {
                            "progress": progress,
                            "log": f"Đang render: {progress}%"
                        }
                    }
                )
                
                # Đợi một khoảng thời gian trước khi kiểm tra lại
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"Lỗi khi kiểm tra trạng thái render: {str(e)}")
                await asyncio.sleep(interval)
        
        # Nếu hết số lần kiểm tra mà vẫn chưa xong
        self.video_collection.update_one(
            {"_id": ObjectId(video_id)},
            {
                "$set": {
                    "status": "failed",
                    "log": "Hết thời gian chờ render"
                }
            }
        )

    def _validate_inputs(self, data: Dict[str, Any]) -> bool:
        """
        Kiểm tra tính hợp lệ của các input
        """
        try:
            # Kiểm tra các trường bắt buộc
            required_fields = ["job_id", "script_id", "segments"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Thiếu trường bắt buộc: {field}")
            
            # Kiểm tra segments
            if not isinstance(data["segments"], list) or len(data["segments"]) == 0:
                raise ValueError("Segments phải là một mảng không rỗng")
            
            # Kiểm tra từng segment
            for i, segment in enumerate(data["segments"]):
                # Kiểm tra các trường bắt buộc của segment
                segment_fields = ["index", "script", "image", "audio", "duration"]
                for field in segment_fields:
                    if field not in segment:
                        raise ValueError(f"Segment {i} thiếu trường bắt buộc: {field}")
                
                # Kiểm tra kiểu dữ liệu
                if not isinstance(segment["index"], int):
                    raise ValueError(f"Index của segment {i} phải là số nguyên")
                if not isinstance(segment["script"], str):
                    raise ValueError(f"Script của segment {i} phải là chuỗi")
                if not isinstance(segment["duration"], (int, float)) or segment["duration"] <= 0:
                    raise ValueError(f"Duration của segment {i} phải là số dương")
            
            return True
            
        except Exception as e:
            raise ValueError(f"Lỗi khi kiểm tra input: {str(e)}")

    async def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin trạng thái của video từ database
        Args:
            video_id: ID của video cần kiểm tra
        Returns:
            Dict chứa thông tin trạng thái video
        """
        try:
            # Kiểm tra ObjectId hợp lệ
            ObjectId(video_id)
            
            # Tìm video trong database
            video = self.video_collection.find_one({"_id": ObjectId(video_id)})
            if not video:
                raise ValueError(f"Không tìm thấy video với ID: {video_id}")
            
            # Nếu video đang trong quá trình render, kiểm tra trạng thái từ Shotstack
            if video.get("status") == "processing" and "render_id" in video:
                render_status = self.shotstack.get_render_status(video["render_id"])
                if render_status:
                    status = render_status.get("response", {}).get("status")
                    if status == "done":
                        # Cập nhật trạng thái và URL video
                        self.video_collection.update_one(
                            {"_id": ObjectId(video_id)},
                            {
                                "$set": {
                                    "status": "done",
                                    "outputPath": render_status["response"]["url"],
                                    "progress": 100,
                                    "log": "Hoàn thành!"
                                }
                            }
                        )
                    elif status == "failed":
                        self.video_collection.update_one(
                            {"_id": ObjectId(video_id)},
                            {
                                "$set": {
                                    "status": "failed",
                                    "log": f"Lỗi render: {render_status.get('response', {}).get('error', 'Không xác định')}"
                                }
                            }
                        )
            
            # Lấy thông tin cập nhật từ database
            video = self.video_collection.find_one({"_id": ObjectId(video_id)})
            return {
                "videoId": video_id,
                "status": video.get("status", "unknown"),
                "progress": video.get("progress", 0),
                "log": video.get("log", "Không có thông tin")
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi lấy trạng thái video: {str(e)}")

    async def get_video_detail(self, video_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết của video từ database
        Args:
            video_id: ID của video cần lấy thông tin
        Returns:
            Dict chứa thông tin chi tiết video
        """
        try:
            # Kiểm tra ObjectId hợp lệ
            ObjectId(video_id)
            # Tìm video trong database
            video = self.video_collection.find_one({"_id": ObjectId(video_id)})
            if not video:
                raise ValueError(f"Không tìm thấy video với ID: {video_id}")
            
            return {
                "videoId": video_id,
                "job_id": video.get("job_id", ""),
                "script_id": video.get("script_id", ""),
                "url": video.get("outputPath", ""),
                "status": video.get("status", "unknown"),
                "duration": video.get("duration", 0),
                "createdAt": video.get("createdAt", datetime.now())
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi lấy thông tin video: {str(e)}")

    async def get_video_preview(self, video_id: str) -> Dict[str, str]:
        """
        Lấy URL stream xem trước video
        Args:
            video_id: ID của video cần xem trước
        Returns:
            Dict chứa URL stream
        """
        try:
            # Kiểm tra ObjectId hợp lệ
            ObjectId(video_id)
            
            # Tìm video trong database
            video = self.video_collection.find_one({"_id": ObjectId(video_id)})
            if not video:
                raise ValueError(f"Không tìm thấy video với ID: {video_id}")
            
            # Kiểm tra trạng thái video
            if video.get("status") != "done":
                raise ValueError("Video chưa sẵn sàng để xem trước")
            
            # Lấy URL video từ outputPath
            video_url = video.get("outputPath")
            if not video_url:
                raise ValueError("Không tìm thấy URL video")
            
            return {
                "streamUrl": video_url
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi lấy URL stream: {str(e)}") 