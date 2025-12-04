#!/usr/bin/env python3
"""
简化的UI测试，不依赖agent，只测试UI组件
"""
import os
import sys
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import flet as ft

def main(page: ft.Page):
    """简化的测试页面"""
    page.title = "CodeAgent UI 测试"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20
    
    # 模拟消息列表
    messages = ft.Column([
        # 用户消息
        ft.Container(
            content=ft.Text("你好，请帮我创建一个Python脚本", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.BLUE_600,
            border_radius=12,
            padding=15,
            margin=ft.margin.symmetric(vertical=5, horizontal=10)
        ),
        # AI回复（带代码块）
        ft.Container(
            content=ft.Column([
                ft.Markdown("我来帮你创建一个Python脚本："),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("```python", color=ft.Colors.BLUE_GREY_700, size=12),
                            ft.Text("Block 0", color=ft.Colors.BLUE_GREY_500, size=12),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(
                            content=ft.Text("""
print("Hello, World!")
import time
time.sleep(1)
print("脚本执行完成！")
                            """.strip(), font_family="Courier New", size=13),
                            bgcolor=ft.Colors.GREY_50,
                            border_radius=8,
                            padding=15,
                            border=ft.border.all(1, ft.Colors.GREY_300)
                        ),
                        ft.Row([
                            ft.ElevatedButton(
                                "确认执行", 
                                icon=ft.Icons.PLAY_ARROW,
                                bgcolor=ft.Colors.GREEN,
                                color=ft.Colors.WHITE
                            ),
                            ft.ElevatedButton(
                                "取消", 
                                icon=ft.Icons.CANCEL,
                                bgcolor=ft.Colors.RED,
                                color=ft.Colors.WHITE
                            )
                        ], alignment=ft.MainAxisAlignment.END)
                    ]),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    border=ft.border.all(2, ft.Colors.BLUE),
                    margin=ft.margin.symmetric(vertical=5)
                )
            ], spacing=10),
            bgcolor=ft.Colors.GREY_100,
            border_radius=12,
            padding=15,
            margin=ft.margin.symmetric(vertical=5, horizontal=10)
        )
    ], scroll=ft.ScrollMode.AUTO, expand=True)
    
    # 输入区域
    message_input = ft.TextField(
        hint_text="输入任务描述...",
        expand=True,
        border_radius=20,
        filled=True,
        bgcolor=ft.Colors.GREY_50
    )
    
    send_button = ft.ElevatedButton(
        "发送",
        icon=ft.Icons.SEND,
        bgcolor=ft.Colors.BLUE_600,
        color=ft.Colors.WHITE,
        on_click=lambda e: print("发送消息:", message_input.value)
    )
    
    # 布局
    page.add(
        ft.Column([
            ft.Text("CodeAgent UI 简化测试", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
            ft.Text("这是一个简化的UI测试界面，用于验证组件功能", size=14, color=ft.Colors.GREY_600),
            ft.Divider(),
            messages,
            ft.Row([message_input, send_button], alignment=ft.MainAxisAlignment.END)
        ], expand=True)
    )
    
    page.update()

if __name__ == "__main__":
    print("启动简化UI测试...")
    ft.app(target=main)
