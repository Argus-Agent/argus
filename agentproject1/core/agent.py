import threading
import time
from datetime import datetime
from typing import Dict, Any
from .state import AgentState, TaskStep


class GUIAgent:
    """GUI Agent核心"""

    def __init__(self, planner, perception, action, message_bus, config):
        self.planner = planner
        self.perception = perception
        self.action = action
        self.message_bus = message_bus
        self.config = config

        self.state = AgentState()
        self.task_queue = []
        self.is_running = False
        self.lock = threading.Lock()

    def process_task(self, task: str):
        """处理任务"""
        if not task:
            return

        with self.lock:
            self.state.current_task = task
            self.state.is_running = True

        # 在新线程中处理任务
        thread = threading.Thread(target=self._process_task_thread, args=(task,))
        thread.daemon = True
        thread.start()

    def _process_task_thread(self, task: str):
        """任务处理线程"""
        try:
            # 1. 发布思考过程
            thought = f"用户要求: {task}"
            self.message_bus.publish("agent_thought", {"thought": thought})

            # 2. 规划下一步
            plan = self.planner.plan(task, self.state)

            # 3. 执行规划
            for step in plan.steps:
                # 发布行动
                self.message_bus.publish("agent_action", {"action": step})

                # 执行行动
                if step == "get_current_time":
                    result = self.action.get_current_time()
                    response = f"当前时间是: {result}"
                elif step == "process_time_request":
                    result = self.perception.interpret_time_request(self.state.current_task)
                    response = result
                else:
                    response = f"执行了操作: {step}"

                # 记录步骤
                task_step = TaskStep(
                    id=str(len(self.state.task_history) + 1),
                    action=step,
                    result=response
                )
                self.state.add_step(task_step)

                # 发布响应
                self.message_bus.publish("agent_response", {"response": response})

                time.sleep(0.5)  # 模拟处理延迟

        except Exception as e:
            error_msg = f"任务处理出错: {str(e)}"
            self.message_bus.publish("agent_response", {"response": error_msg})
        finally:
            with self.lock:
                self.state.is_running = False

    def start_listening(self):
        """开始监听（用于后续扩展）"""
        pass

    def stop(self):
        """停止Agent"""
        with self.lock:
            self.state.is_running = False