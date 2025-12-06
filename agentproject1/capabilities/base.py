# capabilities/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict


class Capability(ABC):
    """能力基类"""
    pass  # 移除 execute 抽象方法


class PerceptionCapability(Capability):
    """感知能力基类"""

    @abstractmethod
    def perceive(self) -> Dict[str, Any]:
        """感知环境"""
        pass


class ReasoningCapability(Capability):
    """推理能力基类"""

    @abstractmethod
    def reason(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """推理分析"""
        pass


class ActionCapability(Capability):
    """行动能力基类"""

    @abstractmethod
    def act(self, command: Dict[str, Any]) -> Any:
        """执行行动"""
        pass