from typing import Dict, Any, Callable, List
import threading


class MessageBus:
    """消息总线 - 简化版事件系统"""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        with self.lock:
            if event_type in self.subscribers:
                self.subscribers[event_type].remove(callback)

    def publish(self, event_type: str, data: Dict[str, Any]):
        """发布事件"""
        with self.lock:
            if event_type in self.subscribers:
                for callback in self.subscribers[event_type]:
                    try:
                        callback(data)
                    except Exception as e:
                        print(f"Error in callback for {event_type}: {e}")