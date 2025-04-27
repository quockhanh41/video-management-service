from pymongo import MongoClient
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    _instance: Optional['MongoDB'] = None
    _client: Optional[MongoClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            # Lấy thông tin kết nối từ biến môi trường
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/video_db")
            
            # Kết nối MongoDB
            self._client = MongoClient(mongo_uri)
            self.db = self._client.get_database()
    
    def get_collection(self, collection_name: str):
        return self.db[collection_name]
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None 