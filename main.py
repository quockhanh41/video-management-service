from fastapi import FastAPI, HTTPException
from routes.video_routes import router as video_router
from service.message_service import MessageService
from service.video_service import VideoService
import threading
from contextlib import asynccontextmanager
import config.moviepy_config  # Import cấu hình MoviePy

# Khởi tạo services
message_service = MessageService()
video_service = VideoService()

async def process_video(message):
    """Callback function để xử lý video"""
    await video_service._create_video({
        "video_id": message.video_id,
        "data": message.data
    })

def run_consumer():
    """Chạy consumer trong một thread riêng"""
    try:
        # Kết nối đến RabbitMQ
        message_service.connect()
        
        # Thiết lập callback xử lý video
        message_service.set_callback(process_video)
        
        # Bắt đầu consume messages
        message_service.consume_messages()
    except Exception as e:
        print(f"Lỗi trong consumer thread: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    # Startup
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    print("Consumer đã được khởi động")
    
    yield
    
    # Shutdown
    message_service.close()
    print("Consumer đã được đóng")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Endpoint kiểm tra trạng thái hoạt động của ứng dụng"""
    return {"status": "healthy"}

# Include routers
app.include_router(video_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000) 