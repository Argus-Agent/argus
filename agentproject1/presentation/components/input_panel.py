import flet as ft


class InputPanel(ft.Container):
    """输入面板组件"""

    def __init__(self, on_send_message):
        super().__init__(padding=10, bgcolor=ft.Colors.GREY_300)

        self.on_send_message = on_send_message
        self.input_field = ft.TextField(
            hint_text="输入任务指令，如：获取当前时间",
            expand=True,
            multiline=False,
            on_submit=self._handle_send
        )

        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND,  # 改为 ft.Icons.SEND
            on_click=self._handle_send
        )

        self.content = ft.Row([
            self.input_field,
            self.send_button
        ])

    def _handle_send(self, e):
        """处理发送消息"""
        text = self.input_field.value.strip()
        if text:
            self.on_send_message(text)
            self.input_field.value = ""
            self.input_field.update()