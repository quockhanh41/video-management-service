# Video Generation API

API để tạo video tự động từ script, hình ảnh và âm thanh.

## Cài đặt

1. Clone repository:
```bash
git clone [repository-url]
```

2. Tạo môi trường ảo:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Tạo file `.env`:
```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CLOUDINARY_NOTIFICATION_URL=your_notification_url
```

## Các Endpoint

### 1. Tạo Video
```http
POST /api/video/generate
```

Request body:
```json
{
  "scriptId": "script_42",
  "segments": [
    {
      "index": 0,
      "script": "Xin chào mọi người",
      "image": "https://example.com/image1.jpg",
      "audio": "https://example.com/audio1.mp3",
      "duration": 5.0,
      "transition": {
        "type": "fade",
        "duration": 1.0
      }
    }
  ],
  "subtitle": {
    "enabled": true,
    "style": {
      "font": "Arial",
      "size": 24,
      "color": "white",
      "background": "black",
      "position": "bottom"
    }
  },
  "videoSettings": {
    "maxAudioSpeed": 1.5,
    "resolution": "1920x1080",
    "frameRate": 30,
    "bitrate": "5000k",
    "audioMismatchStrategy": "extendDuration"
  },
  "backgroundMusic": "https://example.com/music.mp3"
}
```

Response:
```json
{
  "message": "Đang tiến hành tạo video...",
  "videoId": "vid_321"
}
```

### 2. Theo dõi Trạng thái Video
```http
GET /api/video/status/{videoId}
```

Response:
```json
{
  "videoId": "vid_321",
  "status": "processing",
  "progress": 70,
  "log": "Đang ghép hình ảnh với âm thanh"
}
```

### 3. Lấy Thông tin Chi tiết Video
```http
GET /api/video/{videoId}
```

Response:
```json
{
  "videoId": "vid_321",
  "scriptId": "script_42",
  "url": "https://cdn.example.com/videos/vid_321.mp4",
  "status": "done",
  "duration": 134,
  "createdAt": "2025-04-10T10:00:00Z"
}
```

### 4. Xem trước Video
```http
GET /api/video/preview/{videoId}
```

Response:
```json
{
  "streamUrl": "https://res.cloudinary.com/mycloud/video/upload/sp_full_hd/videos/vid_321.m3u8",
  "cloudName": "mycloud",
  "publicId": "videos/vid_321"
}
```

## Các Trạng thái Video

- `pending`: Đang chờ xử lý
- `processing`: Đang xử lý
- `done`: Đã hoàn thành
- `failed`: Thất bại

## Các Loại Transition

- `fade`: Làm mờ
- `slide`: Trượt
- `zoom`: Phóng to/thu nhỏ
- `wipe`: Quét
- `dissolve`: Hòa tan
- `fade_to_black`: Làm mờ sang đen

## Các Chiến lược Xử lý Audio

- `extendDuration`: Kéo dài thời lượng
- `trimAudio`: Cắt audio
- `speedUp`: Tăng tốc độ

## Lưu ý

1. Video được tạo với định dạng HLS để hỗ trợ streaming tốt hơn
2. Các file tạm sẽ được tự động xóa sau khi xử lý xong
3. Video được lưu trữ trên Cloudinary với các transformation được tạo trước
4. Cần cấu hình đúng các biến môi trường trong file `.env` 