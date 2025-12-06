import flet as ft


class MessageBubble(ft.Container):
    """消息气泡组件"""

    def __init__(self, message: dict, is_user: bool = True):
        super().__init__(
            padding=10,
            border_radius=15,
            bgcolor=ft.Colors.BLUE_100 if is_user else ft.Colors.GREY_200,  # 改为 ft.Colors
            margin=ft.margin.only(
                left=50 if not is_user else 0,
                right=0 if not is_user else 50,
                top=5,
                bottom=5
            )
        )

        content = message.get('content', '')
        msg_type = message.get('type', 'text')

        if msg_type == 'thought':
            # 思考过程用特殊样式
            self.bgcolor = ft.Colors.AMBER_100  # 改为 ft.Colors
            self.content = ft.Column([
                ft.Text("💭 思考:", weight=ft.FontWeight.BOLD),
                ft.Text(content),
            ], tight=True)
        elif msg_type == 'action':
            # 行动用特殊样式
            self.bgcolor = ft.Colors.GREEN_100  # 改为 ft.Colors
            self.content = ft.Column([
                ft.Text("⚡ 行动:", weight=ft.FontWeight.BOLD),
                ft.Text(content),
            ], tight=True)
        else:
            # 普通消息
            self.content = ft.Text(content)