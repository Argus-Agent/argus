import flet as ft
from app.application import create_app
from app.di import Container
import yaml
import os


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main(page: ft.Page):
    """主函数 - Flet应用入口"""
    # 加载配置
    config = load_config()

    # 创建依赖注入容器
    container = Container()
    container.config.from_dict(config)

    # 创建并启动应用
    app = create_app(page, container)
    app.run()


if __name__ == "__main__":
    # 启动Flet应用
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
        assets_dir="assets"
    )