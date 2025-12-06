import flet as ft
from datetime import datetime
from presentation.components.chat_window import ChatWindow
from presentation.components.input_panel import InputPanel


class MainPage(ft.Column):
    """主页面"""

    def __init__(self, agent, message_bus, config):
        super().__init__(expand=True)

        self.agent = agent
        self.message_bus = message_bus
        self.config = config

        # 创建UI组件
        self.chat_window = ChatWindow()
        self.input_panel = InputPanel(self._send_user_message)

        # 设置布局
        self.expand = True
        self.controls = [
            self._build_header(),
            self.chat_window,
            self.input_panel
        ]

        # 订阅Agent消息
        self._setup_message_subscriptions()

    def _build_header(self):
        """构建页面头部"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SMART_TOY, size=30),  # 改为 ft.Icons.SMART_TOY
                ft.Text("GUIAgent Demo", size=24, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=15,
            bgcolor=ft.Colors.BLUE_500,
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )

    def _send_user_message(self, text: str):
        """发送用户消息"""
        if not text:
            return

        # 显示用户消息
        user_msg = {
            "type": "user",
            "content": text,
            "timestamp": str(datetime.now())
        }
        self.chat_window.add_message(user_msg, is_user=True)

        # 发送给Agent处理
        self.agent.process_task(text)

    def _setup_message_subscriptions(self):
        """设置消息订阅"""
        self.message_bus.subscribe("agent_thought", self._handle_agent_thought)
        self.message_bus.subscribe("agent_action", self._handle_agent_action)
        self.message_bus.subscribe("agent_response", self._handle_agent_response)

    def _handle_agent_thought(self, data):
        """处理Agent思考过程"""
        thought_msg = {
            "type": "thought",
            "content": data.get("thought", ""),
            "timestamp": str(datetime.now())
        }
        self.chat_window.add_message(thought_msg, is_user=False)

    def _handle_agent_action(self, data):
        """处理Agent行动"""
        action_msg = {
            "type": "action",
            "content": f"执行: {data.get('action', '')}",
            "timestamp": str(datetime.now())
        }
        self.chat_window.add_message(action_msg, is_user=False)

    def _handle_agent_response(self, data):
        """处理Agent响应"""
        response_msg = {
            "type": "agent",
            "content": data.get("response", ""),
            "timestamp": str(datetime.now())
        }
        self.chat_window.add_message(response_msg, is_user=False)

    def build(self):
        """构建页面（兼容性方法）"""
        return self