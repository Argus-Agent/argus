from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class TaskStep:
    """任务步骤"""
    id: str
    action: str
    result: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


@dataclass
class AgentState:
    """Agent状态"""
    current_task: Optional[str] = None
    task_history: List[TaskStep] = field(default_factory=list)
    is_running: bool = False
    current_goal: Optional[str] = None
    error_context: Optional[str] = None

    def add_step(self, step: TaskStep):
        """添加步骤到历史"""
        self.task_history.append(step)
        if len(self.task_history) > 100:  # 限制历史长度
            self.task_history.pop(0)