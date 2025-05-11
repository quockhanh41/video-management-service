from fastapi import FastAPI
from routes.video_routes import router as video_router
from routes.youtube_routes import router as youtube_router
from service.video_service import VideoService
import sys
import platform

# Khởi tạo services
video_service = VideoService()

app = FastAPI()

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
