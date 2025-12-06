import flet as ft
from datetime import datetime


class ChatWindow(ft.Container):
    """聊天窗口组件"""

    def __init__(self):
        super().__init__(expand=True, padding=10)

        self.message_list = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=True
        )

        # 保存欢迎消息，但不立即添加
        self.welcome_msg = {
            "type": "system",
            "content": "欢迎使用GUIAgent！输入'获取当前时间'试试看。",
            "timestamp": str(datetime.now())
        }

        self.content = self.message_list

    def did_mount(self):
        """控件挂载到页面后调用"""
        # 此时控件已添加到页面，可以安全地添加欢迎消息
        self._add_welcome_message()

    def _add_welcome_message(self):
        """添加欢迎消息（内部方法）"""
        if self.welcome_msg:
            # 使用安全的添加方法
            self._safe_add_message(self.welcome_msg, is_user=False)
            self.welcome_msg = None

    def _safe_add_message(self, message: dict, is_user: bool = True):
        """安全添加消息（不立即更新）"""
        from presentation.components.message_bubble import MessageBubble
        bubble = MessageBubble(message, is_user)
        self.message_list.controls.append(bubble)

    def add_message(self, message: dict, is_user: bool = True):
        """添加消息到聊天窗口（公开方法）"""
        self._safe_add_message(message, is_user)
        # 只有页面存在时才更新
        if self.page is not None:
            self.message_list.update()

    def clear_messages(self):
        """清空消息"""
        self.message_list.controls.clear()
        if self.page is not None:
            self.message_list.update()