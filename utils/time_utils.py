from datetime import datetime, timezone, timedelta
from typing import Union

def to_vietnam_time(dt: Union[datetime, str]) -> datetime:
    """
    Chuyển đổi thời gian sang giờ Việt Nam (UTC+7)
    Args:
        dt: Thời gian cần chuyển đổi (datetime hoặc string ISO format)
    Returns:
        Datetime object với timezone Việt Nam
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    # Nếu datetime không có timezone, giả sử là UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Chuyển sang giờ Việt Nam (UTC+7)
    vn_time = dt.astimezone(timezone(timedelta(hours=7)))
    
    return vn_time

def get_current_vn_time() -> datetime:
    """Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7)"""
    return datetime.now(timezone(timedelta(hours=7)))

def format_vn_time(dt: datetime) -> str:
    """Định dạng thời gian theo format HH:mm:ss dd/MM/yyyy"""
    vn_dt = to_vietnam_time(dt)
    return vn_dt.strftime("%H:%M:%S %d/%m/%Y") 