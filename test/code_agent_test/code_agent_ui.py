import asyncio
import base64
import threading
import queue
import time
import flet as ft
import markdown
from typing import Optional, Dict, List, Any
from core.llm.code.agent import CodeAgent

# 使用Markdown进行代码高亮，无需额外依赖

class CodeBlock:
    """代码块组件"""
    def __init__(self, block_id: int, code: str, language: str):
        self.block_id = block_id
        self.code = code
        self.language = language.lower()
        self.is_highlighted = False
        self.is_executing = False
        self.execution_result = ft.Column([])
        
        # 生成高亮代码
        code_content = self._highlight_code(code, language)
        
        # 代码块容器
        self.container = ft.Container(
            content=ft.Column([
                # 代码块头部
                ft.Row([
                    ft.Text(f"```{language}", color=ft.Colors.BLUE_GREY_700, size=12),
                    ft.Text(f"Block {block_id}", color=ft.Colors.BLUE_GREY_500, size=12),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                # 代码内容
                ft.Container(
                    content=code_content,
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=8,
                    padding=15,
                    border=ft.border.all(1, ft.Colors.GREY_300)
                ),
                # 控制按钮区域
                ft.Row([], alignment=ft.MainAxisAlignment.END),
                # 执行结果区域
                self.execution_result
            ]),
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
            margin=ft.margin.symmetric(vertical=5)
        )
        
        # 控制按钮
        self.approve_btn = ft.ElevatedButton(
            "确认执行", 
            icon=ft.Icons.PLAY_ARROW,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE,
            on_click=self._on_approve
        )
        
        self.deny_btn = ft.ElevatedButton(
            "取消", 
            icon=ft.Icons.CANCEL,
            bgcolor=ft.Colors.RED,
            color=ft.Colors.WHITE,
            on_click=self._on_deny
        )
    
    def highlight(self):
        """高亮代码块"""
        self.is_highlighted = True
        self.container.border = ft.border.all(2, ft.Colors.BLUE)
        self.container.bgcolor = ft.Colors.BLUE_50
    
    def unhighlight(self):
        """取消高亮"""
        self.is_highlighted = False
        self.container.border = ft.border.all(1, ft.Colors.GREY_300)
        self.container.bgcolor = ft.Colors.WHITE
    
    def show_controls(self):
        """显示控制按钮"""
        control_row = self.container.content.controls[2]
        control_row.controls = [self.approve_btn, self.deny_btn]
        control_row.update()
    
    def hide_controls(self):
        """隐藏控制按钮"""
        control_row = self.container.content.controls[2]
        control_row.controls = []
        control_row.update()
    
    def set_executing(self, executing: bool):
        """设置执行状态"""
        self.is_executing = executing
        if executing:
            self.show_controls()
    
    def add_execution_result(self, result_type: str, content: str):
        """添加执行结果"""
        if result_type == "text":
            result_text = ft.Text(content, font_family="Courier New", size=12, color=ft.Colors.BLACK87)
            result_container = ft.Container(
                content=result_text,
                bgcolor=ft.Colors.GREY_100,
                border_radius=4,
                padding=10,
                margin=ft.margin.only(top=5)
            )
            self.execution_result.controls.append(result_container)
        elif result_type in ["image/png", "image/jpeg"]:
            # 处理base64图片
            try:
                image_bytes = base64.b64decode(content)
                image = ft.Image(
                    data_base64=content,
                    width=400,
                    height=300,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=4
                )
                image_container = ft.Container(
                    content=image,
                    margin=ft.margin.only(top=5)
                )
                self.execution_result.controls.append(image_container)
            except Exception as e:
                error_text = ft.Text(f"图片显示错误: {str(e)}", color=ft.Colors.RED, size=12)
                self.execution_result.controls.append(error_text)
        
        self.execution_result.update()
    
    def _on_approve(self, e):
        """确认执行"""
        if hasattr(self, 'on_approve_callback'):
            self.on_approve_callback(self.block_id)
    
    def _on_deny(self, e):
        """拒绝执行"""
        if hasattr(self, 'on_deny_callback'):
            self.on_deny_callback(self.block_id)
    
    def _highlight_code(self, code: str, language: str):
        """代码高亮 - 使用Markdown显示"""
        # 使用Markdown组件显示代码，简洁且稳定
        return ft.Markdown(
            f'```{language}\n{code}\n```',
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
        )


class ChatMessage:
    """聊天消息组件"""
    def __init__(self, user_text: str, is_user: bool = True):
        self.is_user = is_user
        self.user_text = user_text
        self.ai_content = ""
        self.code_blocks: List[CodeBlock] = []
        self.current_block_id = 0
        
        if is_user:
            self.content = ft.Container(
                content=ft.Text(user_text, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE_600,
                border_radius=12,
                padding=15,
                margin=ft.margin.symmetric(vertical=5, horizontal=10)
            )
        else:
            self.content = ft.Container(
                content=ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO),
                bgcolor=ft.Colors.GREY_100,
                border_radius=12,
                padding=15,
                margin=ft.margin.symmetric(vertical=5, horizontal=10),
                width=float('inf')
            )
    
    def add_ai_content(self, content: str):
        """添加AI内容"""
        if content == "[BEGIN]":
            self.ai_content = ""
            # 创建AI消息容器
            text_container = ft.Container(
                content=ft.Column([], scroll=ft.ScrollMode.AUTO),
                expand=True
            )
            self.content.content.controls.append(text_container)
        elif content == "[END]":
            # 渲染最终的markdown
            self._render_markdown()
        else:
            self.ai_content += content
            # 实时显示纯文本
            if len(self.content.content.controls) > 0:
                text_container = self.content.content.controls[-1]
                if len(text_container.content.controls) == 0:
                    text_container.content.controls.append(
                        ft.Text(self.ai_content, selectable=True)
                    )
                else:
                    text_container.content.controls[0].value = self.ai_content
                text_container.update()
    
    def _render_markdown(self):
        """渲染Markdown内容"""
        try:
            # 清空当前内容
            self.content.content.controls = []
            
            # 解析代码块
            import re
            code_pattern = r"```(\w*)\n([\s\S]*?)\n```"
            code_matches = list(re.finditer(code_pattern, self.ai_content))
            
            current_pos = 0
            
            for i, match in enumerate(code_matches):
                # 添加代码块前的文本
                if match.start() > current_pos:
                    text = self.ai_content[current_pos:match.start()]
                    if text.strip():
                        text_element = ft.Markdown(text, selectable=True)
                        self.content.content.controls.append(text_element)
                
                # 添加代码块
                lang = match.group(1) or "text"
                code = match.group(2)
                code_block = CodeBlock(i, code, lang)
                self.code_blocks.append(code_block)
                self.content.content.controls.append(code_block.container)
                
                current_pos = match.end()
            
            # 添加剩余文本
            if current_pos < len(self.ai_content):
                remaining_text = self.ai_content[current_pos:]
                if remaining_text.strip():
                    text_element = ft.Markdown(remaining_text, selectable=True)
                    self.content.content.controls.append(text_element)
            
            self.content.update()
            
        except Exception as e:
            # 如果markdown解析失败，显示原始文本
            text_element = ft.Text(self.ai_content, selectable=True)
            self.content.content.controls = [text_element]
            self.content.update()
    
    def get_code_block(self, block_id: int) -> Optional[CodeBlock]:
        """获取指定ID的代码块"""
        for block in self.code_blocks:
            if block.block_id == block_id:
                return block
        return None


class CodeAgentUI:
    """CodeAgent UI主界面"""
    def __init__(self, page: ft.Page):
        self.page = page
        self.agent = CodeAgent()
        self.is_running = False
        self.current_message: Optional[ChatMessage] = None
        
        # 消息队列
        self.message_from_client = queue.Queue()
        self.message_to_client = queue.Queue()
        
        # UI组件
        self.chat_list = ft.Column([], scroll=ft.ScrollMode.AUTO, expand=True)
        self.message_input = ft.TextField(
            hint_text="输入任务描述...",
            expand=True,
            border_radius=20,
            filled=True,
            bgcolor=ft.Colors.GREY_50
        )
        self.send_button = ft.ElevatedButton(
            "发送",
            icon=ft.Icons.SEND,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            on_click=self._send_message,
            disabled=False
        )
        
        self._setup_ui()
        self._start_message_listener()
    
    def _setup_ui(self):
        """设置UI"""
        self.page.title = "CodeAgent 测试界面"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.vertical_alignment = ft.MainAxisAlignment.END
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.padding = 10
        
        # 主要内容区域
        main_content = ft.Container(
            content=self.chat_list,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_300),
            expand=True
        )
        
        # 输入区域
        input_row = ft.Row([
            self.message_input,
            self.send_button
        ], alignment=ft.MainAxisAlignment.END)
        
        input_container = ft.Container(
            content=input_row,
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.GREY_300),
            margin=ft.margin.only(top=10)
        )
        
        # 布局
        self.page.add(
            ft.Column([
                ft.Text("CodeAgent 测试界面", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                main_content,
                input_container
            ], expand=True)
        )
        
        self.page.update()
    
    def _start_message_listener(self):
        """启动消息监听线程"""
        def listener():
            while True:
                try:
                    message = self.message_to_client.get(timeout=0.1)
                    self._handle_message(message)
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"消息处理错误: {e}")
        
        thread = threading.Thread(target=listener, daemon=True)
        thread.start()
    
    def _handle_message(self, message: Dict[str, Any]):
        """处理来自Agent的消息"""
        try:
            name = message.get("name", "")
            msg_type = message.get("type", "")
            content = message.get("content", "")
            
            if name != "CodeAgent":
                return
            
            if msg_type == "status":
                self._handle_status_message(content)
            elif msg_type == "ai_content":
                if self.current_message:
                    self.current_message.add_ai_content(content)
                    self._scroll_to_bottom()
            elif msg_type == "request":
                self._handle_request_message(content)
            elif msg_type == "text":
                if self.current_message:
                    # 查找当前正在执行的代码块
                    for block in self.current_message.code_blocks:
                        if block.is_executing:
                            block.add_execution_result("text", content)
                            self._scroll_to_bottom()
                            break
            elif msg_type in ["image/png", "image/jpeg"]:
                if self.current_message:
                    for block in self.current_message.code_blocks:
                        if block.is_executing:
                            block.add_execution_result(msg_type, content)
                            self._scroll_to_bottom()
                            break
            
            # 更新页面
            self.page.update()
            
        except Exception as e:
            print(f"UI更新错误: {e}")
            self.page.update()
    
    def _handle_status_message(self, content: str):
        """处理状态消息"""
        if content == "[START]":
            self.is_running = True
            self.send_button.text = "停止"
            self.send_button.icon = ft.Icons.STOP
            self.send_button.bgcolor = ft.Colors.RED
            self.send_button.on_click = self._stop_agent
            self.send_button.update()
        elif content == "[STOP]":
            self.is_running = False
            self.send_button.text = "发送"
            self.send_button.icon = ft.Icons.SEND
            self.send_button.bgcolor = ft.Colors.BLUE_600
            self.send_button.on_click = self._send_message
            self.send_button.update()
        elif content.startswith("[BLOCK"):
            # 处理代码块高亮
            try:
                # 解析 [BLOCK0] 格式
                if content.endswith("]"):
                    block_id_str = content[6:-1]  # 去掉 [BLOCK 和 ]
                    block_id = int(block_id_str)
                    print(f"收到代码块状态消息: BLOCK{block_id}")
                    
                    if self.current_message:
                        block = self.current_message.get_code_block(block_id)
                        if block:
                            print(f"找到代码块 {block_id}，设置高亮和执行状态")
                            block.highlight()
                            block.set_executing(True)
                        else:
                            print(f"未找到代码块 {block_id}")
                    else:
                        print("没有当前消息")
                else:
                    print(f"代码块状态格式错误: {content}")
            except Exception as e:
                print(f"处理代码块状态时出错: {e}")
    
    def _handle_request_message(self, content: str):
        """处理请求消息"""
        if content.endswith("need_permission"):
            try:
                block_id = int(content[6:6+content[6:].find("]")])
                if self.current_message:
                    block = self.current_message.get_code_block(block_id)
                    if block:
                        block.show_controls()
                        # 设置回调
                        block.on_approve_callback = self._approve_code_block
                        block.on_deny_callback = self._deny_code_block
            except:
                pass
    
    def _approve_code_block(self, block_id: int):
        """批准执行代码块"""
        print("approve message sent to agent")
        self.message_from_client.put({
            "name": "CodeAgent",
            "type": "request", 
            "content": "approve"
        })
        if self.current_message:
            block = self.current_message.get_code_block(block_id)
            if block:
                block.hide_controls()
                block.unhighlight()
    
    def _deny_code_block(self, block_id: int):
        """拒绝执行代码块"""
        print("deny message sent to")
        self.message_from_client.put({
            "name": "CodeAgent",
            "type": "request",
            "content": "deny"
        })
        if self.current_message:
            block = self.current_message.get_code_block(block_id)
            if block:
                block.hide_controls()
                block.unhighlight()
    
    def _send_message(self, e):
        """发送消息"""
        text = self.message_input.value.strip()
        if not text:
            return
        
        # 清空输入框
        self.message_input.value = ""
        self.message_input.update()
        
        # 添加用户消息
        user_message = ChatMessage(text, is_user=True)
        self.chat_list.controls.append(user_message.content)
        
        # 添加AI响应消息
        ai_message = ChatMessage("", is_user=False)
        self.current_message = ai_message
        self.chat_list.controls.append(ai_message.content)
        
        self._scroll_to_bottom()
        
        # 启动Agent任务
        def run_agent():
            try:
                self.agent.task(text, self.message_from_client, self.message_to_client)
            except Exception as e:
                print(f"Agent执行错误: {e}")
        
        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()
    
    def _stop_agent(self, e):
        """停止Agent"""
        self.message_from_client.put({
            "name": "CodeAgent",
            "type": "request",
            "content": "stop_agent"
        })
    
    def _scroll_to_bottom(self):
        """滚动到底部"""
        try:
            self.chat_list.scroll_to(offset=-1, duration=300)
            self.page.update()
        except Exception as e:
            print(f"滚动错误: {e}")
            self.page.update()


def main(page: ft.Page):
    """主函数"""
    app = CodeAgentUI(page)
    

if __name__ == "__main__":
    ft.app(target=main)
