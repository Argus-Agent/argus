import flet as ft


class Application:
    """应用组装器"""

    def __init__(self, page: ft.Page, container):
        self.page = page
        self.container = container
        self.setup_page()
        self.setup_ui()

    def setup_page(self):
        """配置Flet页面"""
        config = self.container.config()
        self.page.title = config['app']['name']
        self.page.window_width = config['ui']['window_width']
        self.page.window_height = config['ui']['window_height']
        self.page.theme_mode = ft.ThemeMode.LIGHT

    def setup_ui(self):
        """设置UI界面"""
        main_page = self.container.main_page()
        self.page.add(main_page.build())

    def run(self):
        """运行应用"""
        # 启动Agent的消息监听
        agent = self.container.agent()
        agent.start_listening()


def create_app(page: ft.Page, container) -> Application:
    """创建应用实例"""
    return Application(page, container)