from service.video_service import VideoService

class VideoController:
    def __init__(self):
        self.video_service = VideoService()
    
    async def generate_video(self, data: dict):
        return await self.video_service.generate_video(data)
    
    async def get_video_status(self, video_id: str):
        return await self.video_service.get_video_status(video_id)
    
    async def get_video_preview(self, video_id: str):
        return await self.video_service.get_video_preview(video_id)
    
    async def get_video_detail(self, video_id: str):
        return await self.video_service.get_video_detail(video_id)
    
    async def delete_video(self, video_id: str):
        return await self.video_service.delete_video(video_id) 