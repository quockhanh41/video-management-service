from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import os
from typing import Dict, Any
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self, access_token=None, refresh_token=None, client_id=None, client_secret=None, token_uri=None):
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        self.API_SERVICE_NAME = 'youtube'
        self.API_VERSION = 'v3'
        self.credentials = None
        self.youtube = None
        
        logger.info("Khởi tạo YouTubeService với các thông tin:")
        logger.info(f"Client ID: {client_id[:5]}... (đã ẩn)")
        logger.info(f"Token URI: {token_uri}")
        logger.info(f"Access Token tồn tại: {bool(access_token)}")
        logger.info(f"Refresh Token tồn tại: {bool(refresh_token)}")
        
        if access_token and refresh_token and client_id and client_secret and token_uri:
            try:
                self.credentials = Credentials(
                    token=access_token,
                    refresh_token=refresh_token,
                    token_uri=token_uri,
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=self.SCOPES
                )
                logger.info("Đã tạo credentials thành công")
            except Exception as e:
                logger.error(f"Lỗi khi tạo credentials: {str(e)}")
                raise

    def _get_authenticated_service(self):
        if self.youtube:
            logger.info("Sử dụng service đã được xác thực trước đó")
            return self.youtube
            
        if not self.credentials:
            logger.error("Thiếu thông tin xác thực YouTube")
            raise Exception("Thiếu thông tin xác thực YouTube (access_token, refresh_token, client_id, client_secret, token_uri)")
            
        try:
            logger.info("Đang tạo YouTube service mới...")
            logger.info(f"Token URI: {self.credentials.token_uri}")
            logger.info(f"Client ID: {self.credentials.client_id[:5]}... (đã ẩn)")
            logger.info(f"Access Token tồn tại: {bool(self.credentials.token)}")
            logger.info(f"Refresh Token tồn tại: {bool(self.credentials.refresh_token)}")
            logger.info(f"Token hết hạn: {self.credentials.expired}")
            
            self.youtube = build(
                self.API_SERVICE_NAME,
                self.API_VERSION,
                credentials=self.credentials
            )
            logger.info("Đã tạo YouTube service thành công")
            return self.youtube
        except Exception as e:
            logger.error(f"Lỗi khi tạo YouTube service: {str(e)}")
            if hasattr(e, 'resp'):
                logger.error(f"Response status: {e.resp.status}")
                logger.error(f"Response content: {e.content}")
            raise

    async def upload_video(self, video_path: str, title: str, description: str, 
                          category_id: str = "22", privacy_status: str = "private",
                          tags: list = None) -> Dict[str, Any]:
        try:
            logger.info(f"Bắt đầu upload video: {title}")
            logger.info(f"Đường dẫn video: {video_path}")
            logger.info(f"Privacy status: {privacy_status}")
            
            youtube = self._get_authenticated_service()
            
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'categoryId': category_id,
                    'tags': tags or []
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            logger.info("Đang chuẩn bị media file...")
            media = MediaFileUpload(
                video_path,
                mimetype='video/mp4',
                resumable=True
            )
            
            logger.info("Đang gửi request upload...")
            request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            logger.info("Đang thực hiện upload...")
            response = request.execute()
            
            logger.info(f"Upload thành công! Video ID: {response['id']}")
            return {
                'videoId': response['id'],
                'title': response['snippet']['title'],
                'description': response['snippet']['description'],
                'privacyStatus': response['status']['privacyStatus'],
                'url': f"https://www.youtube.com/watch?v={response['id']}"
            }
        except Exception as e:
            logger.error(f"Lỗi chi tiết khi upload video: {str(e)}")
            logger.error(f"Loại lỗi: {type(e).__name__}")
            if hasattr(e, 'resp'):
                logger.error(f"Response status: {e.resp.status}")
                logger.error(f"Response content: {e.content}")
            raise Exception(f"Lỗi khi upload video lên YouTube: {str(e)}")

    async def update_video(self, video_id: str, title: str = None, 
                          description: str = None, privacy_status: str = None,
                          tags: list = None) -> Dict[str, Any]:
        try:
            youtube = self._get_authenticated_service()
            video_response = youtube.videos().list(
                part='snippet,status',
                id=video_id
            ).execute()
            if not video_response['items']:
                raise Exception(f"Không tìm thấy video với ID: {video_id}")
            video = video_response['items'][0]
            body = {
                'id': video_id,
                'snippet': video['snippet'],
                'status': video['status']
            }
            if title:
                body['snippet']['title'] = title
            if description:
                body['snippet']['description'] = description
            if tags:
                body['snippet']['tags'] = tags
            if privacy_status:
                body['status']['privacyStatus'] = privacy_status
            response = youtube.videos().update(
                part=','.join(body.keys()),
                body=body
            ).execute()
            return {
                'videoId': response['id'],
                'title': response['snippet']['title'],
                'description': response['snippet']['description'],
                'privacyStatus': response['status']['privacyStatus'],
                'url': f"https://www.youtube.com/watch?v={response['id']}"
            }
        except Exception as e:
            raise Exception(f"Lỗi khi cập nhật video trên YouTube: {str(e)}")

    async def delete_video(self, video_id: str) -> bool:
        try:
            youtube = self._get_authenticated_service()
            youtube.videos().delete(
                id=video_id
            ).execute()
            return True
        except Exception as e:
            raise Exception(f"Lỗi khi xóa video trên YouTube: {str(e)}") 