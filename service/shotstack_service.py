import os
import requests
import json
import time
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

class ShotstackService:
    def __init__(self):
        self.api_key = os.getenv("SHOTSTACK_API_KEY")
        self.environment = os.getenv("SHOTSTACK_ENVIRONMENT", "PRODUCTION")
        self.api_url = "https://api.shotstack.io/v1/render" if self.environment == "PRODUCTION" else "https://api.sandbox.shotstack.io/v1/render"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }

    def create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def create_timeline(self, segments, background_music=None, subtitle_enabled=False, resolution="1080", aspect_ratio="16:9"):
        """
        Tạo timeline cho video từ danh sách segments và nhạc nền, đúng chuẩn Shotstack
        """
        clips = []
        audio_clips = []
        current_time = 0

        for idx, segment in enumerate(segments):
            # Clip hình ảnh
            image_clip = {
                "asset": {
                    "type": "image",
                    "src": segment["image"]
                },
                "start": current_time,
                "length": segment["duration"],
                "fit": "cover"
            }
            # Thêm transition cho các clip từ clip thứ 2 trở đi
            if idx > 0:
                image_clip["transition"] = {"in": "fade", "out": "fade"}
            clips.append(image_clip)

            # Clip phụ đề (nếu bật)
            if subtitle_enabled:
                subtitle_clip = {
                    "asset": {
                        "type": "title",
                        "text": segment["script"],
                        "style": "minimal",
                        "color": "#FFFFFF",
                        "background": "#000000"
                    },
                    "start": current_time,
                    "length": segment["duration"],
                    "position": "bottom"
                }
                clips.append(subtitle_clip)

            # Clip audio cho từng segment
            audio_clip = {
                "asset": {
                    "type": "audio",
                    "src": segment["audio"],
                },
                "start": current_time,
                "length": segment["duration"]
            }
            audio_clips.append(audio_clip)

            current_time += segment["duration"]

        # Nhạc nền
        if background_music:
            background_music_clip = {
                "asset": {
                    "type": "audio",
                    "src": background_music,
                    "volume": 0.2
                },
                "start": 0,
                "length": current_time
            }
            audio_clips.append(background_music_clip)

        return {
            "timeline": {
                "tracks": [
                    {
                        "clips": clips
                    },
                    {
                        "clips": audio_clips
                    }
                ]
            },
            "output": {
                "format": "mp4",
                "resolution": resolution,
                "aspectRatio": aspect_ratio
            }
        }

    def submit_render(self, timeline_data):
        """
        Gửi request render video đến Shotstack API
        """
        session = self.create_session()
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                print(f"Thử kết nối lần {attempt + 1}/{max_retries}...")
                response = session.post(self.api_url, headers=self.headers, json=timeline_data, timeout=30)
                response.raise_for_status()
                print("✅ Render submitted successfully")
                return response.json()
            except requests.exceptions.ConnectionError as e:
                print(f"❌ Lỗi kết nối: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Đợi {retry_delay} giây trước khi thử lại...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise Exception("Đã hết số lần thử lại. Vui lòng kiểm tra kết nối mạng của bạn.")
            except requests.exceptions.HTTPError as e:
                print("❌ HTTP Error:", e)
                print("Response Body:", response.text)
                raise
            except Exception as e:
                print("❌ Other Error:", e)
                raise

    def get_render_status(self, render_id):
        """
        Kiểm tra trạng thái render của video
        """
        try:
            response = requests.get(
                f"{self.api_url}/{render_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi kiểm tra trạng thái: {str(e)}")
            return None 