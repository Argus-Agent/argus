import flet as ft
import threading
import logging
import queue
import time
import ctypes
from ctypes import windll, wintypes
import sys
import os
import dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


from core.llm.gui.agent import GUIAgent

# Constants for SetWindowDisplayAffinity
WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011

def main(page: ft.Page):
    page.title = "GUI Agent Test"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 800
    page.window_left = 100
    page.window_top = 100
    
    # Try to set window display affinity
    # We need to wait a bit for the window to be created and title to be set
    def set_affinity():
        time.sleep(1)
        hwnd = windll.user32.FindWindowW(None, page.title)
        if hwnd:
            ret = windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            if ret:
                print(f"SetWindowDisplayAffinity success for hwnd {hwnd}")
            else:
                print(f"SetWindowDisplayAffinity failed for hwnd {hwnd}")
        else:
            print("Could not find window handle to set display affinity.")
    
    threading.Thread(target=set_affinity, daemon=True).start()

    # Agent setup
    client_to_agent = queue.Queue()
    agent_to_client = queue.Queue()
    agent = GUIAgent()
    
    chat_list = ft.ListView(expand=True, spacing=10, auto_scroll=True)
    user_input = ft.TextField(hint_text="Enter task...", expand=True, on_submit=lambda e: send_message())
    send_button = ft.IconButton(icon=ft.Icons.SEND, on_click=lambda e: send_message())
    
    is_running = False

    def send_message():
        nonlocal is_running
        if not user_input.value and not is_running:
            return
        
        if is_running:
            # Stop agent
            client_to_agent.put({"name": "GUIAgent", "type": "request", "content": "stop_agent"})
            return

        task_desc = user_input.value
        user_input.value = ""
        user_input.disabled = True
        send_button.icon = ft.Icons.STOP
        page.update()

        # Add user message
        chat_list.controls.append(ft.Row([
            ft.Container(
                content=ft.Text(task_desc, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE,
                padding=10,
                border_radius=10
            )
        ], alignment=ft.MainAxisAlignment.END))
        
        # Add placeholder for AI message
        response_column = ft.Column(spacing=10)
        chat_list.controls.append(ft.Row([
            ft.Container(
                content=response_column,
                bgcolor=ft.Colors.GREY_200,
                padding=10,
                border_radius=10,
                expand=True
            )
        ], alignment=ft.MainAxisAlignment.START))
        page.update()

        # Start agent thread
        is_running = True
        threading.Thread(target=agent.task, args=(task_desc, client_to_agent, agent_to_client), daemon=True).start()
        
        # Start polling thread
        threading.Thread(target=poll_messages, args=(response_column,), daemon=True).start()

    def poll_messages(response_column):
        nonlocal is_running
        current_text_control = None
        
        while True:
            try:
                msg = agent_to_client.get(timeout=0.1)
                
                if msg["type"] == "status":
                    status = msg["content"]
                    if status == "[STOP]":
                        is_running = False
                        user_input.disabled = False
                        send_button.icon = ft.Icons.SEND
                        page.update()
                        break
                
                elif msg["type"] in ["image/png", "image/jpeg"]:
                    # Add image to response column
                    img_control = ft.Image(
                        src_base64=msg["content"],
                        width=400,
                        fit=ft.ImageFit.CONTAIN,
                        border_radius=5
                    )
                    response_column.controls.append(img_control)
                    page.update()
                    chat_list.scroll_to(offset=-1)
                    # Reset text control so next text starts new block
                    current_text_control = None

                elif msg["type"] == "ai_content":
                    if current_text_control is None:
                        current_text_control = ft.Markdown(
                            "", 
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            on_tap_link=lambda e: page.launch_url(e.data)
                        )
                        response_column.controls.append(current_text_control)
                        page.update()
                        chat_list.scroll_to(offset=-1)
                    
                    current_text_control.value += msg["content"]
                    current_text_control.update()
                    chat_list.scroll_to(offset=-1)
                    
                elif msg["type"] == "action_point":
                    content = msg["content"]
                    handle_action_point(content)
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error polling: {e}")
                break

    def show_click_indicator(x, y):
        def _draw():
            x_int, y_int = int(x), int(y)
            hdc = windll.user32.GetDC(0)
            if not hdc: return
            
            # Red pen, width 3. Color is 0x00BBGGRR, so 0x000000FF is Red.
            pen = windll.gdi32.CreatePen(0, 3, 0x000000FF)
            brush = windll.gdi32.GetStockObject(5) # NULL_BRUSH
            
            old_pen = windll.gdi32.SelectObject(hdc, pen)
            old_brush = windll.gdi32.SelectObject(hdc, brush)
            
            radius = 15
            windll.gdi32.Ellipse(hdc, x_int - radius, y_int - radius, x_int + radius, y_int + radius)
            
            windll.gdi32.SelectObject(hdc, old_pen)
            windll.gdi32.SelectObject(hdc, old_brush)
            windll.gdi32.DeleteObject(pen)
            windll.user32.ReleaseDC(0, hdc)
            
            time.sleep(0.5)
            
            # Invalidate to clear
            rect = wintypes.RECT(x_int - radius - 5, y_int - radius - 5, x_int + radius + 5, y_int + radius + 5)
            windll.user32.InvalidateRect(0, ctypes.byref(rect), True)
            
        threading.Thread(target=_draw, daemon=True).start()

    def handle_action_point(content):
        x = content.get("x")
        y = content.get("y")
        if x is None or y is None:
            return
            
        show_click_indicator(x, y)

        # Check if point is inside window
        # Note: page.window_left/top might need to be fetched dynamically if user moved window
        # But Flet properties usually update.
        wx = page.window_left
        wy = page.window_top
        ww = page.window_width
        wh = page.window_height
        
        if wx is None: wx = 0
        if wy is None: wy = 0
        
        # Simple collision check
        # Add some padding
        padding = 20
        if (wx - padding) <= x <= (wx + ww + padding) and (wy - padding) <= y <= (wy + wh + padding):
            # Avoid
            screen_width = windll.user32.GetSystemMetrics(0)
            print(f"Avoiding click at {x},{y}. Current window: {wx},{wy}")
            if x < screen_width / 2:
                # Move to right
                page.window_left = screen_width - ww - 50
            else:
                # Move to left
                page.window_left = 50
            page.update()

    page.add(
        ft.Container(
            content=chat_list,
            expand=True,
            padding=10
        ),
        ft.Container(
            content=ft.Row([
                user_input,
                send_button
            ]),
            padding=10
        )
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ft.app(target=main)
