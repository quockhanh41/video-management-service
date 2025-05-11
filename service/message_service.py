import pika
import json
from typing import Dict, Any, Callable
import os
from dotenv import load_dotenv
from models.message_model import VideoMessage
from service.video_service import VideoService
import asyncio
from bson.objectid import ObjectId
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class MessageService:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = "video_creation_queue_test"
        self.callback = None
        self.video_service = VideoService()
        
    def connect(self):
        """Kết nối đến RabbitMQ server"""
        try:
            # Lấy thông tin kết nối từ biến môi trường
            rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
            self.connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            self.channel = self.connection.channel()
            
            # Khai báo queue
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            print("Đã kết nối đến RabbitMQ")
            
        except Exception as e:
            print(f"Lỗi khi kết nối RabbitMQ: {str(e)}")
            raise
            
    def close(self):
        """Đóng kết nối RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            
    def publish_message(self, message: Dict[str, Any]):
        """Gửi message vào queue"""
        try:
            if not self.channel:
                self.connect()
                
            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            print(f"Đã gửi message: {message['video_id']}")
            
        except Exception as e:
            print(f"Lỗi khi gửi message: {str(e)}")
            raise
            
    def set_callback(self, callback: Callable[[VideoMessage], None]):
        """Thiết lập callback function để xử lý message"""
        self.callback = callback
            
    def consume_messages(self):
        """Xử lý các message trong queue"""
        def message_callback(ch, method, properties, body):
            try:
                # Parse message
                message_data = json.loads(body)
                message = VideoMessage(**message_data)
                print(f"Đang xử lý video: {message.video_id}")
                
                # Gọi callback function nếu có
                if self.callback:
                    # Tạo event loop mới để chạy async function
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self.callback(message))
                    finally:
                        loop.close()
                
                # Xác nhận đã xử lý xong
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"Đã xử lý xong video: {message.video_id}")
                
            except Exception as e:
                print(f"Lỗi khi xử lý message: {str(e)}")
                # Nếu có lỗi, reject message và đưa vào queue lại
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                
        try:
            if not self.channel:
                self.connect()
                
            # Thiết lập prefetch count
            self.channel.basic_qos(prefetch_count=1)
            
            # Bắt đầu consume
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=message_callback
            )
            
            print("Bắt đầu lắng nghe messages...")
            self.channel.start_consuming()
            
        except Exception as e:
            print(f"Lỗi khi consume messages: {str(e)}")
            raise 

    async def _process_message(self, message: Dict[str, Any]):
        """
        Xử lý message từ queue
        """
        try:
            # Lấy thông tin video từ MongoDB
            video = self.video_collection.find_one({"_id": ObjectId(message["video_id"])})
            if not video:
                raise ValueError(f"Video {message['video_id']} không tồn tại")

            # Cập nhật trạng thái đang xử lý
            self.video_service._update_video_status({
                "video_id": str(video["_id"]),
                "status": "processing",
                "progress": 0,
                "log": "Đang xử lý video..."
            })

            # Xử lý video
            await self.video_service.process_video(message)

        except Exception as e:
            logger.error(f"Lỗi xử lý message: {str(e)}")
            # Cập nhật trạng thái lỗi với progress 0
            self.video_service._update_video_status({
                "video_id": message["video_id"],
                "status": "error",
                "progress": 0,
                "log": f"Lỗi: {str(e)}"
            }) 