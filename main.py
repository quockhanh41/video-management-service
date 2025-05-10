from fastapi import FastAPI, HTTPException
from routes.video_routes import router as video_router
from routes.youtube_routes import router as youtube_router
from service.message_service import MessageService
from service.video_service import VideoService
import threading
from contextlib import asynccontextmanager
import config.moviepy_config  # Import cấu hình MoviePy
import sys
import platform

# Khởi tạo services
message_service = MessageService()
video_service = VideoService()

async def process_video(message):
    """Callback function để xử lý video"""
    await video_service._create_video({
        "video_id": message.video_id,
        "data": message.data
    })

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Thiết lập callback
    message_service.set_callback(process_video)
    
    # Khởi tạo worker thread
    worker = threading.Thread(
        target=message_service.consume_messages,
        daemon=True
    )
    worker.start()
    yield
    # Cleanup khi shutdown
    message_service.close()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Endpoint kiểm tra trạng thái hoạt động của ứng dụng"""
    return {"status": "healthy"}

@app.get("/info")
async def get_info():
    """Endpoint hiển thị thông tin về môi trường chạy"""
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "python_implementation": platform.python_implementation(),
        "python_compiler": platform.python_compiler()
    }

# Include routers
app.include_router(video_router, prefix="/api/v1")
app.include_router(youtube_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000) 