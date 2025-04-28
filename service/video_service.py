from models.video_model import VideoModel
from typing import Dict, Any, List
import os
import requests
from datetime import datetime
from bson import ObjectId
from config.mongodb import MongoDB
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, VideoFileClip, TextClip, CompositeVideoClip, CompositeAudioClip, VideoClip
import concurrent.futures
from functools import lru_cache
import tempfile
from pathlib import Path
from models.message_model import VideoMessage
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from config.cloudinary import CloudinaryConfig

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
                script_id=data["scriptId"],
                scripts=data["scripts"],
                images=data["images"],
                audios=data["audios"],
                backgroundMusic=data["backgroundMusic"],
                subtitle=data["subtitle"],
                status="pending",
                progress=0,
                log="Đang chờ xử lý..."
            )
            
            # Tạo video_id
            video_id = str(ObjectId())
            
            # Lưu thông tin video vào MongoDB
            video_data = {
                "_id": ObjectId(video_id),
                "scriptId": data["scriptId"],
                "scripts": data["scripts"],
                "images": data["images"],
                "audios": data["audios"],
                "backgroundMusic": data["backgroundMusic"],
                "subtitle": data["subtitle"],
                "status": video_model.status,
                "progress": video_model.progress,
                "log": video_model.log,
                "createdAt": datetime.now(),
                "outputPath": video_model.output_video
            }
            self.video_collection.insert_one(video_data)
            
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
        # Kiểm tra số lượng scripts, images và audios phải bằng nhau
        if len(data["scripts"]) != len(data["images"]) or \
           len(data["scripts"]) != len(data["audios"]):
            raise ValueError("Số lượng scripts, images và audios phải bằng nhau")
        
        # Kiểm tra các link images và audios
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Kiểm tra images
            image_futures = [executor.submit(self._validate_url, url, "ảnh") for url in data["images"]]
            # Kiểm tra audios
            audio_futures = [executor.submit(self._validate_url, url, "audio") for url in data["audios"]]
            
            # Đợi tất cả các kiểm tra hoàn thành
            concurrent.futures.wait(image_futures + audio_futures)
            
            # Kiểm tra kết quả
            for future in image_futures + audio_futures:
                if future.exception():
                    raise future.exception()
            
        return True

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

    def _add_subtitle(self, clip: VideoClip, text: str, duration: float) -> VideoClip:
        """
        Thêm phụ đề vào video clip
        """
        try:
            # Tạo text clip với font mặc định
            txt_clip = TextClip(
                text,
                fontsize=70,
                color='white',
                bg_color='black',
                font='Arial',
                method='caption',
                size=(clip.w, None),
                align='center'
            )
            
            # Đặt vị trí và thời gian
            txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(duration)
            
            # Kết hợp với video
            return CompositeVideoClip([clip, txt_clip])
        except Exception as e:
            print(f"Lỗi khi thêm phụ đề: {str(e)}")
            return clip  # Trả về clip gốc nếu có lỗi

    def _add_background_music(self, clip: VideoClip, music_path: str) -> VideoClip:
        """
        Thêm nhạc nền vào video
        """
        # Tải nhạc nền
        music = AudioFileClip(music_path)
        
        # Lặp nhạc nếu cần
        if music.duration < clip.duration:
            music = music.loop(duration=clip.duration)
        else:
            music = music.subclip(0, clip.duration)
        
        # Giảm âm lượng nhạc nền
        music = music.volumex(0.3)
        
        # Kết hợp với audio gốc
        final_audio = CompositeAudioClip([clip.audio, music])
        
        # Gán audio mới vào video
        return clip.set_audio(final_audio)

    async def _create_video(self, message: Dict[str, Any]) -> str:
        """
        Tạo video từ model sử dụng moviepy
        """
        video_id = message["video_id"]
        data = message["data"]
        temp_files = []  # Danh sách các file tạm cần dọn dẹp
        
        try:
            # Cập nhật trạng thái đang xử lý
            self._update_video_status({
                "video_id": video_id,
                "status": "processing",
                "progress": 0,
                "log": "Bắt đầu xử lý video..."
            })
            
            # Tạo model
            video_model = VideoModel(
                script_id=data["scriptId"],
                scripts=data["scripts"],
                images=data["images"],
                audios=data["audios"],
                backgroundMusic=data["backgroundMusic"],
                subtitle=data["subtitle"],
                status="processing",
                progress=0,
                log="Bắt đầu xử lý video..."
            )
            
            # 1. Download images and audios
            video_model.progress = 20
            video_model.log = "Đang tải hình ảnh và âm thanh..."
            self._update_video_status({
                "video_id": video_id,
                "status": video_model.status,
                "progress": video_model.progress,
                "log": video_model.log
            })
            
            # Tải các file song song
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Tải images
                image_futures = [
                    executor.submit(self._download_file, url, "image", i)
                    for i, url in enumerate(video_model.images)
                ]
                # Tải audios
                audio_futures = [
                    executor.submit(self._download_file, url, "audio", i)
                    for i, url in enumerate(video_model.audios)
                ]
                
                # Lấy kết quả
                temp_images = [f.result() for f in image_futures]
                temp_audios = [f.result() for f in audio_futures]
                temp_files.extend(temp_images + temp_audios)
            
            # 2. Generate video for each script-image-audio combination
            video_model.progress = 50
            video_model.log = "Đang tạo video cho từng đoạn..."
            self._update_video_status({
                "video_id": video_id,
                "status": video_model.status,
                "progress": video_model.progress,
                "log": video_model.log
            })
            
            # Tạo video cho từng cặp script-image-audio
            temp_videos = []
            for i, (image_path, audio_path) in enumerate(zip(temp_images, temp_audios)):
                with AudioFileClip(audio_path) as audio:
                    audio_duration = audio.duration

                # Resize ảnh trước khi tạo clip
                img = Image.open(image_path)
                img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
                img_path = str(self.temp_dir / f"resized_{i}.jpg")
                img.save(img_path)
                temp_files.append(img_path)
                
                # Tạo clip từ ảnh đã resize
                clip = ImageClip(img_path).set_duration(audio_duration).on_color(
                    size=(1920, 1080), color=(0,0,0), pos='center'
                )
                
                # Thêm hiệu ứng crossfade nếu không phải ảnh đầu tiên
                if i > 0:
                    clip = clip.crossfadein(0.5)
                
                # Thêm phụ đề nếu có
                if video_model.subtitle:
                    clip = self._add_subtitle(clip, video_model.scripts[i], audio_duration)
                
                # Lưu video tạm
                temp_video_path = str(self.temp_dir / f"video_{i}.mp4")
                clip.write_videofile(
                    temp_video_path,
                    fps=24,
                    codec="libx264",
                    audio=False,
                    preset="ultrafast"  # Tối ưu tốc độ encoding
                )
                temp_videos.append(temp_video_path)
                temp_files.append(temp_video_path)

                # Combine video and audio
                with VideoFileClip(temp_video_path) as video, AudioFileClip(audio_path) as audio:
                    final = video.set_audio(audio).set_duration(min(video.duration, audio.duration))
                    final.write_videofile(
                        temp_video_path,
                        fps=24,
                        codec="libx264",
                        audio_codec="aac",
                        preset="ultrafast"
                    )
            
            # 3. Combine all videos
            video_model.progress = 70
            video_model.log = "Đang ghép hình ảnh với âm thanh..."
            self._update_video_status({
                "video_id": video_id,
                "status": video_model.status,
                "progress": video_model.progress,
                "log": video_model.log
            })
            
            # Nối các video lại với nhau
            with concatenate_videoclips([VideoFileClip(v) for v in temp_videos], method="compose") as final_video:
                # 4. Add background music if needed
                if video_model.backgroundMusic:
                    video_model.progress = 85
                    video_model.log = "Đang thêm nhạc nền..."
                    self._update_video_status({
                        "video_id": video_id,
                        "status": video_model.status,
                        "progress": video_model.progress,
                        "log": video_model.log
                    })
                    
                    # Tải nhạc nền
                    music_path = self._download_file(video_model.backgroundMusic, "music", 0)
                    temp_files.append(music_path)
                    
                    # Thêm nhạc nền
                    final_video = self._add_background_music(final_video, music_path)
                
                # 5. Export final video
                video_model.progress = 100
                video_model.status = "done"
                video_model.log = "Hoàn thành tạo video!"
                self._update_video_status({
                    "video_id": video_id,
                    "status": video_model.status,
                    "progress": video_model.progress,
                    "log": video_model.log
                })
                
                final_video.write_videofile(
                    video_model.output_video,
                    fps=24,
                    codec="libx264",
                    audio_codec="aac",
                    preset="ultrafast"
                )
            
            # 6. Upload video lên Cloudinary
            video_model.log = "Đang upload video lên Cloudinary..."
            self._update_video_status({
                "video_id": video_id,
                "status": video_model.status,
                "progress": video_model.progress,
                "log": video_model.log
            })
            
            # Upload video
            upload_result = self.cloudinary.upload_file(
                video_model.output_video,
                folder="videos"
            )
            
            # 7. Cập nhật MongoDB với URL video
            self.video_collection.update_one(
                {"_id": ObjectId(video_id)},
                {
                    "$set": {
                        "output_video": upload_result["secure_url"],
                    }
                }
            )
            
            # 8. Cleanup
            self._cleanup(temp_files)
            
            return video_id
            
        except Exception as e:
            # Cleanup trong trường hợp lỗi
            self._cleanup(temp_files)
            
            self._update_video_status({
                "video_id": video_id,
                "status": "failed",
                "progress": video_model.progress,
                "log": f"Lỗi: {str(e)}"
            })
            raise Exception(f"Lỗi khi tạo video: {str(e)}")

    def _update_video_status(self, data: Dict[str, Any]):
        """
        Cập nhật trạng thái video trong MongoDB
        """
        self.video_collection.update_one(
            {"_id": ObjectId(data["video_id"])},
            {
                "$set": {
                    "status": data["status"],
                    "progress": data["progress"],
                    "log": data["log"]
                }
            }
        )

    def _cleanup(self, files: List[str]):
        """
        Dọn dẹp các file tạm
        """
        for file_path in files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Lỗi khi xóa file tạm {file_path}: {str(e)}") 