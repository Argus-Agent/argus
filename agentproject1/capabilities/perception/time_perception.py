# capabilities/perception/time_perception.py
from capabilities.base import PerceptionCapability
from datetime import datetime
import re
from typing import Dict, Any


class TimePerception(PerceptionCapability):
    """时间感知能力"""

    def perceive(self) -> Dict[str, Any]:
        """感知当前时间"""
        now = datetime.now()
        return {
            "current_time": now,
            "timestamp": now.isoformat(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second
        }

    def interpret_time_request(self, request: str) -> str:
        """解释时间请求"""
        request_lower = request.lower()

        if "时间" in request_lower or "time" in request_lower:
            if "当前" in request_lower or "现在" in request_lower or "current" in request_lower:
                return "这是一个获取当前时间的请求，我将执行获取时间操作。"
            elif "今天" in request_lower or "today" in request_lower:
                return "您想了解今天的日期信息。"
            elif "明天" in request_lower or "tomorrow" in request_lower:
                return "您想了解明天的日期信息。"

        return f"已收到请求: {request}，正在分析处理中..."