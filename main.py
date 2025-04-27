from fastapi import FastAPI, HTTPException
from models.video_model import VideoModel
from controllers.video_controller import VideoController
from routes.video_routes import router as video_router
from service.message_service import MessageService
from service.video_service import VideoService
import asyncio
import threading
import os

app = FastAPI()

# Khởi tạo services
message_service = MessageService()
video_service = VideoService()

def run_consumer():
    """Chạy consumer trong một thread riêng"""
    try:
        # Kết nối đến RabbitMQ
        message_service.connect()
        
        # Thiết lập callback xử lý video
        message_service.set_callback(lambda message: video_service._create_video({
            "video_id": message.video_id,
            "data": message.data
        }))
        
        message_service.consume_messages()
    except Exception as e:
        print(f"Lỗi trong consumer thread: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Khởi động consumer khi API server khởi động"""
    # Tạo thread mới để chạy consumer
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    print("Consumer đã được khởi động")

@app.on_event("shutdown")
async def shutdown_event():
    """Đóng kết nối khi API server tắt"""
    message_service.close()
    print("Consumer đã được đóng")

# Include routers
app.include_router(video_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000) 