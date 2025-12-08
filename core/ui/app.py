"""
✨ Agent4 Liquid Bar - 苹果液态风格主控条
透明、圆角、可视化反馈
"""

import sys
import os
import queue
import threading
import tkinter as tk
import customtkinter as ctk

# 引入项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from core.agents.smart_router import get_router
    ROUTER_AVAILABLE = True
except:
    ROUTER_AVAILABLE = False

try:
    from core.ui.visualizer import visualizer
    VISUALIZER_AVAILABLE = True
except:
    VISUALIZER_AVAILABLE = False

# 颜色定义
transparent_bg_key = "#000001" # 用于被扣除的透明色

class LiquidBar(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. 窗口基础设置：完全透明 + 无边框
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.config(background=transparent_bg_key)
        self.attributes('-transparentcolor', transparent_bg_key)
        
        # 尺寸
        screen_width = self.winfo_screenwidth()
        self.width_compact = 500
        self.height = 60
        
        self.geometry(f"{self.width_compact}x{self.height}+{screen_width//2 - self.width_compact//2}+50")
        
        # 2. 主容器 (模拟圆角悬浮体)
        # 注意: CustomTkinter的圆角Frame在transparentcolor上有时会有锯齿，
        # 我们使用fg_color与背景色不同来显示。
        self.bar_frame = ctk.CTkFrame(
            self, 
            fg_color="#F0F0F0", # 苹果灰白
            corner_radius=25,
            height=50,
            width=self.width_compact,
            bg_color=transparent_bg_key # 外部透明
        )
        self.bar_frame.pack(fill="both", expand=True, padx=10, pady=5) # 留边距给阴影(虽无真阴影)
        
        # 内部布局
        self.setup_ui()
        self.setup_backend()
        
        # 拖拽支持
        self.bar_frame.bind("<Button-1>", self.start_drag)
        self.bar_frame.bind("<B1-Motion>", self.do_drag)

    def setup_ui(self):
        # 布局容器
        layout = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=15, pady=5)
        
        # 1. 状态灯
        self.status = ctk.CTkLabel(layout, text="●", font=("Arial", 28), text_color="#34C759", width=30)
        self.status.pack(side="left")
        
        # 2. 输入框
        self.entry = ctk.CTkEntry(
            layout, 
            placeholder_text="Agent 4 指令...",
            font=("PingFang SC", 14),
            fg_color="#FFFFFF",
            border_width=0,
            width=280,
            height=36,
            corner_radius=18
        )
        self.entry.pack(side="left", padx=10)
        self.entry.bind("<Return>", self.run_task)
        
        # 3. 运行按钮 (蓝色圆)
        self.btn_run = ctk.CTkButton(
            layout,
            text="➤",
            width=36,
            height=36,
            corner_radius=18,
            fg_color="#007AFF",
            hover_color="#0062CC",
            font=("Arial", 16),
            command=self.run_task
        )
        self.btn_run.pack(side="left", padx=5)
        
        # 4. 中断按钮 (红色圆，默认隐藏，运行时显示)
        self.btn_stop = ctk.CTkButton(
            layout,
            text="■",
            width=36,
            height=36,
            corner_radius=18,
            fg_color="#FF3B30", # Apple Red
            hover_color="#D70015",
            font=("Arial", 12),
            command=self.stop_task
        )
        # pack在run后面，初始隐藏
        
    def setup_backend(self):
        self.msg_from_client = queue.Queue()
        self.msg_to_client = queue.Queue()
        
        self.router = None
        if ROUTER_AVAILABLE:
            try:
                self.router = get_router()
            except:
                self.status.configure(text_color="#FF3B30")
                
        if VISUALIZER_AVAILABLE:
            visualizer.start()
            
        self.check_queue()

    # --- 逻辑 ---
    
    def run_task(self, event=None):
        task = self.entry.get().strip()
        if not task: return
        
        # UI切换到运行态
        self.btn_run.pack_forget()
        self.btn_stop.pack(side="left", padx=5)
        self.status.configure(text_color="#007AFF") # Blue busy
        self.entry.configure(state="disabled", fg_color="#E5E5E5")
        
        threading.Thread(target=self._run_thread, args=(task,), daemon=True).start()
        
    def stop_task(self):
        # 发送停止信号
        self.msg_from_client.put({"name": "User", "type": "request", "content": "stop_agent"})
        # UI立即反馈
        self.reset_ui()
        
    def _run_thread(self, task):
        if self.router:
            self.router.execute_with_fallback(task, self.msg_from_client, self.msg_to_client)

    def reset_ui(self):
        self.btn_stop.pack_forget()
        self.btn_run.pack(side="left", padx=5)
        self.status.configure(text_color="#34C759") # Green ready
        self.entry.configure(state="normal", fg_color="#FFFFFF")

    def check_queue(self):
        try:
            while True:
                msg = self.msg_to_client.get_nowait()
                mtype = msg.get('type')
                content = msg.get('content')
                
                if mtype == "status":
                    if content == "[STOP]":
                        self.reset_ui()
                
                elif mtype == "action_point":
                    # 可视化反馈!
                    if VISUALIZER_AVAILABLE and isinstance(content, dict):
                        x = content.get('x')
                        y = content.get('y')
                        if x and y:
                            visualizer.show_click(x, y)

                elif mtype == "human_intervention_needed":
                    # 简化：只打印日志，或者弹一个Tkinter对话框
                    pass

        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_queue)

    # --- 拖拽 ---
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def do_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
        
    def on_closing(self):
        if VISUALIZER_AVAILABLE:
            visualizer.stop()
        self.destroy()

if __name__ == "__main__":
    app = LiquidBar()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
