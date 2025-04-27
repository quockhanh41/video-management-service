import os
import sys
from pathlib import Path

# Lấy đường dẫn thư mục gốc của project
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from service.message_service import MessageService

def main():
    try:
        # Khởi tạo message service
        message_service = MessageService()
        
        # Kết nối đến RabbitMQ
        message_service.connect()
        
        # Bắt đầu lắng nghe messages
        print("Bắt đầu consumer...")
        message_service.consume_messages()
        
    except KeyboardInterrupt:
        print("\nĐang dừng consumer...")
        message_service.close()
        sys.exit(0)
    except Exception as e:
        print(f"Lỗi: {str(e)}")
        message_service.close()
        sys.exit(1)

if __name__ == "__main__":
    main() 