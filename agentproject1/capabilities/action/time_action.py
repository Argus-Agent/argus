# capabilities/action/time_action.py
from capabilities.base import ActionCapability
from datetime import datetime
from typing import Any, Dict


class TimeAction(ActionCapability):
    """时间行动能力"""

    def get_current_time(self) -> str:
        """获取当前时间"""
        now = datetime.now()

        # 格式化时间显示
        formats = [
            now.strftime("%Y年%m月%d日 %H:%M:%S"),
            now.strftime("%A, %B %d, %Y %I:%M:%S %p"),
            f"时间戳: {now.timestamp()}"
        ]

        return formats[0]  # 返回第一种格式

    def act(self, command: Dict[str, Any]) -> Any:
        """执行行动 - 实现抽象方法"""
        action_type = command.get("type", "")

        if action_type == "get_time":
            return self.get_current_time()
        elif action_type == "format_time":
            return self.format_time(command.get("format", ""))
        else:
            return f"未知的时间操作: {action_type}"

    def format_time(self, fmt: str) -> str:
        """格式化时间"""
        try:
            return datetime.now().strftime(fmt)
        except:
            return "时间格式错误"