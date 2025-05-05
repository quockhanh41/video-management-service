from models.video_model import VideoModel, SubtitleStyle
from typing import Dict, Any, List
import os
import requests
from datetime import datetime
from bson import ObjectId
from config.mongodb import MongoDB
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, TextClip, CompositeVideoClip, CompositeAudioClip, VideoClip, concatenate_audioclips, ColorClip, VideoFileClip
import concurrent.futures
from functools import lru_cache
import tempfile
from pathlib import Path
from config.cloudinary import CloudinaryConfig
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import cloudinary
from service.vid_transition_func import create_transition

class VideoService:
    def __init__(self):
        self.mongodb = MongoDB()
        self.video_collection = self.mongodb.get_collection("videos")
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        self.cloudinary = CloudinaryConfig()
    
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
            ObjectId(data["scriptId"])
            
            # Validate inputs
            self._validate_inputs(data)
            
            # Tạo model
            video_model = VideoModel(
                scriptId=data["scriptId"],
                segments=data["segments"],
                subtitle=data["subtitle"],
                videoSettings=data["videoSettings"],
                backgroundMusic=data["backgroundMusic"],
                status="pending",
                progress=0,
                log="Đang chờ xử lý..."
            )
            
            # Lưu thông tin video vào MongoDB
            video_data = {
                "scriptId": data["scriptId"],
                "segments": data["segments"],
                "subtitle": data["subtitle"],
                "videoSettings": data["videoSettings"],
                "backgroundMusic": data["backgroundMusic"],
                "status": video_model.status,
                "progress": video_model.progress,
                "log": video_model.log,
                "createdAt": datetime.now(),
                "outputPath": video_model.output_video
            }
            result = self.video_collection.insert_one(video_data)
            video_id = str(result.inserted_id)
            
            return {
                "message": "Đang tiến hành tạo video...",
                "videoId": video_id
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi tạo video: {str(e)}")

    def _validate_inputs(self, data: Dict[str, Any]) -> bool:
        """
        Kiểm tra tính hợp lệ của các input
        """
        try:
            # Kiểm tra các trường bắt buộc
            required_fields = ["scriptId", "segments", "subtitle", "videoSettings"]
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
                
                # Kiểm tra kiểu dữ liệu
                if not isinstance(segment["index"], int):
                    raise ValueError(f"Index của segment {i} phải là số nguyên")
                if not isinstance(segment["script"], str):
                    raise ValueError(f"Script của segment {i} phải là chuỗi")
                if not isinstance(segment["duration"], (int, float)) or segment["duration"] <= 0:
                    raise ValueError(f"Duration của segment {i} phải là số dương")
                
                # Kiểm tra transition
                if not isinstance(segment["transition"], dict):
                    raise ValueError(f"Transition của segment {i} phải là một object")
                
                transition_fields = ["type", "duration"]
                for field in transition_fields:
                    if field not in segment["transition"]:
                        raise ValueError(f"Transition của segment {i} thiếu trường bắt buộc: {field}")
                
                if segment["transition"]["type"] not in ["rotation", "rotation_inv", "zoom_in", "zoom_out", "translation", "translation_inv", "long_translation", "long_translation_inv"]:
                    raise ValueError(f"Transition type của segment {i} phải là một trong các giá trị: rotation, rotation_inv, zoom_in, zoom_out, translation, translation_inv, long_translation, long_translation_inv")
                
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
            
            if not isinstance(data["subtitle"]["style"]["size"], int) or data["subtitle"]["style"]["size"] <= 0:
                raise ValueError("Subtitle size phải là số nguyên dương")
            
            if data["subtitle"]["style"]["position"] not in ["bottom", "center"]:
                raise ValueError("Subtitle position phải là 'bottom' hoặc 'center'")
            
            # Kiểm tra video settings
            if not isinstance(data["videoSettings"], dict):
                raise ValueError("Video settings phải là một object")
            
            settings_fields = ["maxAudioSpeed", "resolution", "frameRate", "bitrate", "audioMismatchStrategy"]
            for field in settings_fields:
                if field not in data["videoSettings"]:
                    raise ValueError(f"Video settings thiếu trường bắt buộc: {field}")
            
            if not isinstance(data["videoSettings"]["maxAudioSpeed"], (int, float)) or data["videoSettings"]["maxAudioSpeed"] <= 0:
                raise ValueError("Max audio speed phải là số dương")
            
            if not isinstance(data["videoSettings"]["frameRate"], int) or data["videoSettings"]["frameRate"] <= 0:
                raise ValueError("Frame rate phải là số nguyên dương")
            
            if data["videoSettings"]["audioMismatchStrategy"] not in ["extendDuration", "trimAudio", "speedUp"]:
                raise ValueError("Audio mismatch strategy phải là 'extendDuration', 'trimAudio' hoặc 'speedUp'")
            
            # Kiểm tra các link images và audios
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Kiểm tra images
                image_futures = [executor.submit(self._validate_url, segment["image"], "ảnh") for segment in data["segments"]]
                # Kiểm tra audios
                audio_futures = [executor.submit(self._validate_url, segment["audio"], "audio") for segment in data["segments"]]
                
                # Đợi tất cả các kiểm tra hoàn thành
                concurrent.futures.wait(image_futures + audio_futures)
                
                # Kiểm tra kết quả
                for future in image_futures + audio_futures:
                    if future.exception():
                        raise future.exception()
            
            # Kiểm tra background music nếu có
            if "backgroundMusic" in data and data["backgroundMusic"]:
                self._validate_url(data["backgroundMusic"], "nhạc nền")
            
            return True
            
        except Exception as e:
            raise ValueError(f"Lỗi khi kiểm tra input: {str(e)}")

    @lru_cache(maxsize=128)
    def _validate_url(self, url: str, file_type: str) -> bool:
        """
        Kiểm tra URL có hợp lệ không và cache kết quả
        """
        try:
            response = requests.head(url, timeout=5)
            if response.status_code != 200:
                raise ValueError(f"Link {file_type} không hợp lệ: {url}")
            return True
        except Exception as e:
            raise ValueError(f"Không thể truy cập link {file_type}: {url} - {str(e)}")

    def _download_file(self, url: str, file_type: str, index: int) -> str:
        """
        Tải file từ URL và lưu vào thư mục temp
        """
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Tạo file tạm
            suffix = ".jpg" if file_type == "image" else ".mp3"
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                dir=self.temp_dir
            )
            
            # Tải file theo từng chunk
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            raise Exception(f"Lỗi khi tải {file_type} {index}: {str(e)}")

    def _add_subtitle(self, clip: VideoClip, text: str, duration: float, style: SubtitleStyle) -> VideoClip:
        """
        Thêm phụ đề vào video clip với style tùy chỉnh
        """
        try:
            # Tạo text clip với style được chỉ định
            txt_clip = TextClip(
                text,
                fontsize=style.size,
                color=style.color,
                bg_color=style.background,
                font=style.font,
                method='caption',
                size=(clip.w, None),
                align='center'
            )
            
            # Đặt vị trí và thời gian
            position = ('center', 'bottom') if style.position == "bottom" else ('center', 'center')
            txt_clip = txt_clip.set_position(position).set_duration(duration)
            
            # Kết hợp với video
            return CompositeVideoClip([clip, txt_clip])
        except Exception as e:
            print(f"Lỗi khi thêm phụ đề: {str(e)}")
            return clip  # Trả về clip gốc nếu có lỗi

    def _add_background_music(self, clip: VideoClip, music_path: str) -> VideoClip:
        """
        Thêm nhạc nền vào video
        """
        try:
            # Tải nhạc nền
            music = AudioFileClip(music_path)
            
            # Lặp nhạc nếu cần
            if music.duration < clip.duration:
                # Tính số lần lặp cần thiết
                n_loops = int(clip.duration / music.duration) + 1
                # Tạo danh sách các audio clip
                music_clips = [music] * n_loops
                # Kết hợp các audio clip
                music = concatenate_audioclips(music_clips)
                # Cắt phần thừa
                music = music.subclip(0, clip.duration)
            else:
                music = music.subclip(0, clip.duration)
            
            # Giảm âm lượng nhạc nền
            music = music.volumex(0.3)
            
            # Kết hợp với audio gốc
            final_audio = CompositeAudioClip([clip.audio, music])
            
            # Gán audio mới vào video
            return clip.set_audio(final_audio)
        except Exception as e:
            print(f"Lỗi khi thêm nhạc nền: {str(e)}")
            return clip

    async def _create_video(self, message: Dict[str, Any]) -> str:
        """
        Tạo video từ model sử dụng moviepy
        """
        video_id = message["video_id"]
        data = message["data"]
        final_clip = None
        temp_files = []
        
        try:
            # Tạo model từ data
            video_model = VideoModel(**data)
            
            # Cập nhật trạng thái
            self._update_video_status({
                "video_id": video_id,
                "status": "processing",
                "progress": 0,
                "log": "Đang tải các file..."
            })
            
            # Tải tất cả các file
            for segment in video_model.segments:
                # Tải ảnh
                image_path = self._download_file(segment.image, "image", segment.index)
                temp_files.append(image_path)
                
                # Tải audio
                audio_path = self._download_file(segment.audio, "audio", segment.index)
                temp_files.append(audio_path)
            
            # Tải nhạc nền nếu có
            if video_model.backgroundMusic:
                bg_music_path = self._download_file(video_model.backgroundMusic, "audio", -1)
                temp_files.append(bg_music_path)
            
            # Tạo các video từ ảnh
            clips = []
            for i, segment in enumerate(video_model.segments):
                try:
                    # Tạo image clip
                    image_path = temp_files[i * 2]
                    image_clip = ImageClip(image_path)
                    
                    # Đặt thời lượng cho clip
                    image_clip = image_clip.set_duration(segment.duration)
                    
                    # Đặt FPS
                    image_clip = image_clip.set_fps(video_model.videoSettings.frameRate)
                    
                    # Tạo audio clip
                    audio_path = temp_files[i * 2 + 1]
                    audio_clip = AudioFileClip(audio_path)
                    
                    # Xử lý audio theo chiến lược
                    if audio_clip.duration > segment.duration:
                        if video_model.videoSettings.audioMismatchStrategy == "extendDuration":
                            # Kéo dài image duration = audio duration
                            image_clip = image_clip.set_duration(audio_clip.duration)
                        elif video_model.videoSettings.audioMismatchStrategy == "trimAudio":
                            # Cắt audio
                            audio_clip = audio_clip.subclip(0, segment.duration)
                        else:  # speedUp
                            # Tăng tốc audio
                            speed_factor = audio_clip.duration / segment.duration
                            if speed_factor <= video_model.videoSettings.maxAudioSpeed:
                                audio_clip = audio_clip.speedx(speed_factor)
                            else:
                                # Nếu vượt quá tốc độ tối đa, cắt audio
                                audio_clip = audio_clip.subclip(0, segment.duration)
                    else:
                        # Nếu audio ngắn hơn hoặc bằng segment duration, giữ nguyên
                        audio_clip = audio_clip.set_duration(segment.duration)
                    
                    # Kết hợp image và audio
                    clip = image_clip.set_audio(audio_clip)
                    
                    # Thêm phụ đề nếu được bật
                    if video_model.subtitle.enabled:
                        clip = self._add_subtitle(
                            clip,
                            segment.script,
                            segment.duration,
                            video_model.subtitle.style
                        )
                    
                    clips.append(clip)
                    
                    # Cập nhật tiến độ
                    progress = int((i + 1) / len(video_model.segments) * 100)
                    self._update_video_status({
                        "video_id": video_id,
                        "progress": progress,
                        "log": f"Đang xử lý segment {i + 1}/{len(video_model.segments)}..."
                    })
                except Exception as e:
                    raise Exception(f"Lỗi khi xử lý segment {i}: {str(e)}")
            
            # Tạo transition giữa các video
            final_clips = []
            for i in range(len(clips)):
                if i > 0:  # Thêm transition cho tất cả các clip trừ clip đầu tiên
                    try:
                        # Tạo file video tạm thời cho clip trước
                        temp_video1 = os.path.join(str(self.temp_dir), f"temp_video1_{i}.mp4")
                        clips[i-1].write_videofile(
                            temp_video1,
                            fps=video_model.videoSettings.frameRate,
                            codec='libx264',
                            audio=False
                        )
                        temp_files.append(temp_video1)
                        
                        # Tạo file video tạm thời cho clip hiện tại
                        temp_video2 = os.path.join(str(self.temp_dir), f"temp_video2_{i}.mp4")
                        clips[i].write_videofile(
                            temp_video2,
                            fps=video_model.videoSettings.frameRate,
                            codec='libx264',
                            audio=False
                        )
                        temp_files.append(temp_video2)
                        
                        # Tạo transition video
                        transition_video = create_transition(
                            input_videos=[temp_video1, temp_video2],
                            temp_path=str(self.temp_dir),
                            animation=video_model.segments[i].transition.type,
                            num_frames=30,
                            max_brightness=1.5
                        )
                        
                        # Tạo clip transition
                        transition_clip = VideoFileClip(transition_video)
                        final_clips.append(transition_clip)
                        
                    except Exception as e:
                        print(f"Lỗi khi tạo transition: {str(e)}")
                        # Nếu có lỗi, bỏ qua transition và tiếp tục với clip tiếp theo
                        continue
                
                # Thêm clip hiện tại vào danh sách
                final_clips.append(clips[i])
            
            # Kết hợp tất cả các clip
            final_clip = concatenate_videoclips(final_clips, method="compose")
            
            # Thêm nhạc nền nếu có
            if video_model.backgroundMusic:
                final_clip = self._add_background_music(final_clip, bg_music_path)
            
            # Xuất video
            final_clip.write_videofile(
                video_model.output_video,
                fps=video_model.videoSettings.frameRate,
                codec='libx264',
                audio_codec='aac',
                bitrate=video_model.videoSettings.bitrate,
                threads=24,
                preset='medium'
            )
            
            # Lấy duration của video
            video_model.duration = int(final_clip.duration)
            
            # Upload video lên Cloudinary
            try:
                # Định nghĩa eager transformations cho HLS
                eager_transformations = [
                    {
                        "format": "m3u8",
                        "streaming_profile": "full_hd",
                        "transformation": [
                            {"width": 1920, "height": 1080, "crop": "limit"},
                            {"quality": "auto"},
                            {"fetch_format": "auto"}
                        ]
                    }
                ]
                
                upload_result = self.cloudinary.upload_file(
                    video_model.output_video,
                    folder="videos",
                    eager_transformations=eager_transformations
                )
                
                # Cập nhật outputPath và duration trong MongoDB
                self.video_collection.update_one(
                    {"_id": ObjectId(video_id)},
                    {
                        "$set": {
                            "outputPath": upload_result["secure_url"],
                            "cloudinaryPublicId": upload_result["public_id"],
                            "duration": video_model.duration
                        }
                    }
                )
                
                # Xóa file video local sau khi upload thành công
                if os.path.exists(video_model.output_video):
                    os.remove(video_model.output_video)
                    
            except Exception as e:
                print(f"Lỗi khi upload video lên Cloudinary: {str(e)}")
                raise Exception(f"Lỗi khi upload video: {str(e)}")
            
            # Cập nhật trạng thái hoàn thành
            self._update_video_status({
                "video_id": video_id,
                "status": "done",
                "progress": 100,
                "log": "Hoàn thành!"
            })
            
            return upload_result["secure_url"]
            
        except Exception as e:
            # Cập nhật trạng thái lỗi
            self._update_video_status({
                "video_id": video_id,
                "status": "failed",
                "log": f"Lỗi: {str(e)}"
            })
            raise Exception(f"Lỗi khi tạo video: {str(e)}")
        finally:
            # Dọn dẹp các file tạm và giải phóng tài nguyên
            if final_clip:
                try:
                    final_clip.close()
                except:
                    pass
            self._cleanup(temp_files)

    def _update_video_status(self, data: Dict[str, Any]):
        """
        Cập nhật trạng thái video trong MongoDB
        """
        try:
            update_data = {
                "status": data.get("status", "processing"),
                "log": data.get("log", "")
            }
            
            # Thêm progress nếu có
            if "progress" in data:
                update_data["progress"] = data["progress"]
                
            self.video_collection.update_one(
                {"_id": ObjectId(data["video_id"])},
                {
                    "$set": update_data
                }
            )
        except Exception as e:
            print(f"Lỗi khi cập nhật trạng thái video: {str(e)}")

    def _cleanup(self, files: List[str]):
        """
        Dọn dẹp các file tạm
        """
        import time
        for file_path in files:
            if not os.path.exists(file_path):
                continue
                
            # Thử xóa file nhiều lần nếu cần
            max_retries = 3
            retry_delay = 1  # giây
            
            for i in range(max_retries):
                try:
                    # Đóng file nếu đang mở
                    import gc
                    gc.collect()  # Thu gom rác để đóng các file đang mở
                    time.sleep(retry_delay)  # Đợi một chút
                    
                    # Thử đóng file nếu đang mở
                    try:
                        with open(file_path, 'rb') as f:
                            pass
                    except:
                        pass
                        
                    os.remove(file_path)
                    break  # Thoát vòng lặp nếu xóa thành công
                except Exception as e:
                    if i == max_retries - 1:  # Lần thử cuối cùng
                        print(f"Lỗi khi xóa file tạm {file_path} sau {max_retries} lần thử: {str(e)}")
                    else:
                        time.sleep(retry_delay)  # Đợi trước khi thử lại

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
            
            return {
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
                "scriptId": video.get("scriptId", ""),
                "outputPath": video.get("outputPath", ""),
                "status": video.get("status", "unknown"),
                "duration": video.get("duration", 0),
                "createdAt": video.get("createdAt", datetime.now())
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi lấy thông tin video: {str(e)}")

    async def get_video_preview(self, video_id: str) -> Dict[str, str]:
        """
        Lấy URL stream xem trước video từ Cloudinary
        Args:
            video_id: ID của video cần xem trước
        Returns:
            Dict chứa URL stream, cloud_name và public_id
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
            
            # Lấy public_id từ kết quả upload
            public_id = video.get("cloudinaryPublicId")
            if not public_id:
                raise ValueError("Không tìm thấy public_id của video")
            
            # Lấy cloud_name từ environment
            cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
            if not cloud_name:
                raise ValueError("Không tìm thấy cloud_name trong cấu hình")
            
            # Tạo URL stream HLS
            base_url = f"https://res.cloudinary.com/{cloud_name}/video/upload"
            stream_url = f"{base_url}/sp_full_hd/{public_id}.m3u8"
            
            return {
                "streamUrl": stream_url,
                "cloudName": cloud_name,
                "publicId": public_id
            }
            
        except Exception as e:
            raise Exception(f"Lỗi khi lấy URL stream: {str(e)}") 