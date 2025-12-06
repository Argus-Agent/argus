from datetime import datetime, timedelta

def get_current_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前时间"""
    return datetime.now().strftime(format_str)

def format_time_delta(seconds: int) -> str:
    """格式化时间间隔"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        return f"{seconds // 60}分钟{seconds % 60}秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分钟"

def is_working_hours() -> bool:
    """判断是否为工作时间"""
    now = datetime.now()
    return 9 <= now.hour < 18