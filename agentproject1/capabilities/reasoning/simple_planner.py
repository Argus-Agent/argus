# capabilities/reasoning/simple_planner.py
from dataclasses import dataclass
from typing import List, Dict, Any
from capabilities.base import ReasoningCapability


@dataclass
class Plan:
    """规划结果"""
    steps: List[str]
    confidence: float


class SimplePlanner(ReasoningCapability):
    """简单规划器"""

    def plan(self, task: str, state) -> Plan:
        """规划任务步骤"""
        task_lower = task.lower()

        if "时间" in task_lower or "time" in task_lower:
            return Plan(
                steps=["process_time_request", "get_current_time"],
                confidence=0.9
            )
        else:
            return Plan(
                steps=["analyze_request", "generate_response"],
                confidence=0.7
            )

    def reason(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """推理分析 - 实现抽象方法"""
        task = context.get("task", "")
        task_lower = task.lower()

        if "时间" in task_lower or "time" in task_lower:
            return {
                "analysis": "这是一个时间相关请求",
                "next_action": "get_current_time",
                "confidence": 0.9
            }
        else:
            return {
                "analysis": "无法识别请求类型",
                "next_action": "unknown",
                "confidence": 0.3
            }