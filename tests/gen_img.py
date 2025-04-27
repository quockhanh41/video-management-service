import requests
import base64
from io import BytesIO
from PIL import Image


# Thay thế bằng API key của bạn
API_KEY = "sk-Auy16d8rzfBdRWw1uyF48ylzi5UW6arOgwHIgmFnY6V9kYEi"
API_HOST = "https://api.stability.ai"
ENGINE_ID = "stable-diffusion-v1-6"  # Có thể thay bằng model khác như stable-diffusion-xl-1024-v1-0


def generate_image(prompt, output_file="output.png"):
    # Định nghĩa endpoint
    url = f"{API_HOST}/v1/generation/{ENGINE_ID}/text-to-image"
   
    # Headers cho request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
   
    # Payload với các tham số
    payload = {
        "text_prompts": [
            {
                "text": prompt,
                "weight": 1.0
            }
        ],
        "cfg_scale": 7.5,
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 30,
    }
   
    try:
        # Gửi request đến API
        response = requests.post(url, headers=headers, json=payload)
       
        # Kiểm tra response
        if response.status_code == 200:
            data = response.json()
            # Lấy hình ảnh từ base64
            image_base64 = data["artifacts"][0]["base64"]
            image_data = base64.b64decode(image_base64)
           
            # Lưu hình ảnh
            image = Image.open(BytesIO(image_data))
            image.save(output_file)
            print(f"Hình ảnh đã được lưu tại: {output_file}")
        else:
            print(f"Lỗi: {response.status_code} - {response.text}")
           
    except Exception as e:
        print(f"Đã xảy ra lỗi: {str(e)}")


# Sử dụng hàm
if __name__ == "__main__":
    # Thay đổi prompt theo ý muốn
    prompts = ["Welcome to our beautiful flower presentation! Let's explore the enchanting world of flowers together.",
               "First, we have a stunning rose, the queen of flowers. Its delicate petals and sweet fragrance have captivated hearts for centuries. The rose symbolizes love, passion, and beauty.",
               "Next, we see a vibrant sunflower, standing tall and proud. This magnificent flower follows the sun's path across the sky, bringing warmth and joy to any garden. Sunflowers represent happiness and positivity.",
               "Finally, we admire a graceful lily, with its elegant form and pure white petals. The lily is often associated with purity and renewal, making it a favorite in gardens and floral arrangements.",
               "Thank you for joining us on this floral journey. May these beautiful blooms bring joy to your day!"
               ]
    for i, prompt in enumerate(prompts):
        generate_image(prompt, f"image{i+1}.png")
