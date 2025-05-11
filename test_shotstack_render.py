import os
import requests
import json
import time
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

API_KEY = os.getenv("SHOTSTACK_API_KEY")
ENVIRONMENT = "PRODUCTION"  # Chuyển sang production

# Select the correct API host based on environment
API_URL = "https://api.shotstack.io/v1/render"  # URL production

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

# Sample payload (replace with your real timeline and output)
timeline = {
    "timeline": {
        "tracks": [
            {
                "clips": [
                    {
                        "asset": {
                            "type": "image",
                            "src": "https://res.cloudinary.com/dxpz4afdv/image/upload/v1746913324/video-generator/jholerysfb6rhgqlqngz.png"
                        },
                        "start": 0,
                        "length": 15.24,
                        "transition": {
                            "in": "fade",
                            "out": "fade"
                        },
                        "fit": "cover"
                    },
                    {
                        "asset": {
                            "type": "image",
                            "src": "https://res.cloudinary.com/dxpz4afdv/image/upload/v1746913323/video-generator/ue6iyqycttibkoasdygu.png"
                        },
                        "start": 15.24,
                        "length": 15.216,
                        "transition": {
                            "in": "fade",
                            "out": "fade"
                        },
                        "fit": "cover"
                    },
                    {
                        "asset": {
                            "type": "image",
                            "src": "https://res.cloudinary.com/dxpz4afdv/image/upload/v1746913323/video-generator/gqvwlvdk1mbx5lffmny3.png"
                        },
                        "start": 30.456,
                        "length": 14.592,
                        "transition": {
                            "in": "fade",
                            "out": "fade"
                        },
                        "fit": "cover"
                    },
                    {
                        "asset": {
                            "type": "image",
                            "src": "https://res.cloudinary.com/dxpz4afdv/image/upload/v1746913325/video-generator/rz6htoljsvhb7m8xzypz.png"
                        },
                        "start": 45.048,
                        "length": 14.76,
                        "transition": {
                            "in": "fade",
                            "out": "fade"
                        },
                        "fit": "cover"
                    }
                ]
            },
            {
                "clips": [
                    {
                        "asset": {
                            "type": "audio",
                            "src": "https://res.cloudinary.com/db9cb3rmt/video/upload/v1746913630/voices/hauassqmkqoe1me4erxo.mp3"
                        },
                        "start": 0,
                        "length": 15.24
                    },
                    {
                        "asset": {
                            "type": "audio",
                            "src": "https://res.cloudinary.com/db9cb3rmt/video/upload/v1746913633/voices/uttpvk9iwqm4zaw333ct.mp3"
                        },
                        "start": 15.24,
                        "length": 15.216
                    },
                    {
                        "asset": {
                            "type": "audio",
                            "src": "https://res.cloudinary.com/db9cb3rmt/video/upload/v1746913636/voices/bznt2hwrw4jt7xd6pcrr.mp3"
                        },
                        "start": 30.456,
                        "length": 14.592
                    },
                    {
                        "asset": {
                            "type": "audio",
                            "src": "https://res.cloudinary.com/db9cb3rmt/video/upload/v1746913639/voices/frs4f7aaweqwheklipaj.mp3"
                        },
                        "start": 45.048,
                        "length": 14.76
                    }
                ]
            }
        ]
    },
    "output": {
        "format": "mp4",
        "resolution": "1080",
        "aspectRatio": "16:9"
    }
}

def create_session():
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

def submit_render(timeline_data):
    session = create_session()
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            print(f"Thử kết nối lần {attempt + 1}/{max_retries}...")
            response = session.post(API_URL, headers=HEADERS, json=timeline_data, timeout=30)
            response.raise_for_status()
            print("✅ Render submitted successfully")
            print("Render ID:", response.json()["response"]["id"])
            return response.json()
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Lỗi kết nối: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Đợi {retry_delay} giây trước khi thử lại...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Tăng thời gian chờ mỗi lần thử
            else:
                print("❌ Đã hết số lần thử lại. Vui lòng kiểm tra kết nối mạng của bạn.")
                raise
        except requests.exceptions.HTTPError as e:
            print("❌ HTTP Error:", e)
            print("Response Body:", response.text)
            raise
        except Exception as e:
            print("❌ Other Error:", e)
            raise

def get_render_status(render_id):
    try:
        response = requests.get(
            f"{API_URL}/{render_id}",
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi khi kiểm tra trạng thái: {str(e)}")
        return None

def main():
    print(f"Using environment: {ENVIRONMENT}")
    print(f"Sending request to: {API_URL}")
    response = submit_render(timeline)
    
    if response and "response" in response and "id" in response["response"]:
        render_id = response["response"]["id"]
        print(f"\nRender ID: {render_id}")
        print("\nĐang theo dõi tiến trình render...")
        
        while True:
            status = get_render_status(render_id)
            if not status:
                print("Không thể kiểm tra trạng thái render")
                break
                
            render_status = status.get("response", {}).get("status")
            print(f"Trạng thái: {render_status}")
            
            if render_status == "done":
                print("\n✅ Render hoàn tất!")
                print(f"URL video: {status['response']['url']}")
                break
            elif render_status == "failed":
                print("\n❌ Render thất bại!")
                print(f"Lỗi: {status.get('response', {}).get('error', 'Không xác định')}")
                break
                
            time.sleep(5)  # Đợi 5 giây trước khi kiểm tra lại
    else:
        print("❌ Không thể lấy Render ID từ response")

if __name__ == "__main__":
    # main()
    status = get_render_status("b6a097da-4205-41e8-a3de-a42c4363c48a")
    print(status)
