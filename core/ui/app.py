"""
✨ Agent4 Liquid Bar - Apple Jelly Edition
透明、圆角、可视化反馈、果冻动效、历史记录功能
"""

import sys
import os
import queue
import threading
import json  # [新增] 用于存取历史记录
import tkinter as tk
import customtkinter as ctk
# 新增：环境变量管理
from dotenv import load_dotenv, set_key, find_dotenv

# 1. 环境配置加载
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

# 引入项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

# 尝试导入核心模块
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

# 颜色定义 (更新为果冻风格配色)
THEME = {
    "transparent_bg_key": "#000001",  # 用于被扣除的透明色
    "jelly_bg": "#F5F6FA",  # 奶白色背景
    "jelly_border": "#FFFFFF",  # 高光边框
    "accent_blue": "#007AFF",
    "accent_red": "#FF3B30",
    "accent_green": "#34C759",
    "text_main": "#1D1D1F",
    "text_sub": "#86868B",
    "corner_radius": 32,  # 默认大圆角 (欢迎页用)
    "font_entry": ("PingFang SC", 14),
    "font_btn": ("Arial", 15, "bold")
}


# ==========================================
# [新增] 历史记录管理器
# ==========================================
class HistoryManager:
    def __init__(self, filepath="history.json", max_items=10):
        self.filepath = os.path.join(current_dir, filepath)
        self.max_items = max_items
        self.history = self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def add(self, text):
        if not text: return
        # 移除重复项并置顶
        if text in self.history:
            self.history.remove(text)
        self.history.insert(0, text)
        # 限制数量
        if len(self.history) > self.max_items:
            self.history = self.history[:self.max_items]
        self.save()

    def save(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False)
        except Exception as e:
            print(f"History save failed: {e}")

    def get_all(self):
        return self.history


# ==========================================
# 基础窗口类：封装透明、拖拽与果冻动画
# ==========================================
class JellyBaseWindow(ctk.CTk):
    # [修改] 增加了 corner_radius 和 padding 参数，方便定制形状
    def __init__(self, width, height, center_on_screen=True, top_offset=None, corner_radius=None, padding=15):
        super().__init__()

        # 1. 窗口基础设置：完全透明 + 无边框
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.config(background=THEME["transparent_bg_key"])
        self.attributes('-transparentcolor', THEME["transparent_bg_key"])

        # 尺寸与位置计算
        self.target_w = width
        self.target_h = height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        if center_on_screen:
            # 居中模式 (欢迎页/配置页)
            self.final_x = screen_width // 2 - width // 2
            self.final_y = screen_height // 2 - height // 2
            self.anim_center_x = screen_width // 2
            self.anim_center_y = screen_height // 2
        else:
            # 顶部固定模式 (LiquidBar)
            fixed_y = top_offset if top_offset is not None else 50
            self.final_x = screen_width // 2 - width // 2
            self.final_y = fixed_y
            # 动画中心点
            self.anim_center_x = self.final_x + (width // 2)
            self.anim_center_y = self.final_y + (height // 2)

        # 确定圆角大小 (如果没有指定，就用主题默认的)
        radius = corner_radius if corner_radius is not None else THEME["corner_radius"]

        # 2. 主容器 (模拟圆角果冻体)
        self.bar_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["jelly_bg"],
            corner_radius=radius,
            bg_color=THEME["transparent_bg_key"],  # 外部透明
            border_width=3,  # 高光边框
            border_color=THEME["jelly_border"]
        )
        # [修改] padding 现在是动态的
        self.bar_frame.pack(fill="both", expand=True, padx=padding, pady=padding)

        # 拖拽支持
        self.bar_frame.bind("<Button-1>", self.start_drag)
        self.bar_frame.bind("<B1-Motion>", self.do_drag)

        # 启动入场动画
        self.animation_step = 0
        self.after(10, self.animate_pop_in)

    def animate_pop_in(self):
        """果冻Q弹入场动画"""
        scales = [0.1, 0.4, 0.8, 1.05, 0.98, 1.0]
        if self.animation_step < len(scales):
            scale = scales[self.animation_step]
            curr_w = int(self.target_w * scale)
            curr_h = int(self.target_h * scale)

            x = self.anim_center_x - (curr_w // 2)
            y = self.anim_center_y - (curr_h // 2)

            self.geometry(f"{curr_w}x{curr_h}+{x}+{y}")
            self.animation_step += 1
            self.after(25, self.animate_pop_in)
        else:
            self.geometry(f"{self.target_w}x{self.target_h}+{self.final_x}+{self.final_y}")

    # --- 拖拽逻辑 ---
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def do_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        new_x = self.winfo_x() + deltax
        new_y = self.winfo_y() + deltay
        self.geometry(f"+{new_x}+{new_y}")
        # 更新坐标防止动画重置
        self.final_x = new_x
        self.final_y = new_y
        self.anim_center_x = new_x + (self.target_w // 2)
        self.anim_center_y = new_y + (self.target_h // 2)


# ==========================================
# 欢迎窗口 (Splash Screen)
# ==========================================
class WelcomeWindow(JellyBaseWindow):
    def __init__(self, on_next):
        # 欢迎页保持大圆角和较大的 Padding
        super().__init__(300, 300, center_on_screen=True)
        self.on_next = on_next
        self.setup_ui()
        # 2秒后自动跳转
        self.after(2000, self.auto_transition)

    def setup_ui(self):
        layout = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        layout.pack(expand=True, fill="both")

        ctk.CTkLabel(layout, text="🍮", font=("Arial", 80)).pack(pady=(50, 20))
        ctk.CTkLabel(layout, text="Agent 4", font=("Arial", 30, "bold"), text_color=THEME["text_main"]).pack()
        ctk.CTkLabel(layout, text="Loading...", font=("Arial", 12), text_color=THEME["text_sub"]).pack(side="bottom",
                                                                                                       pady=30)

    def auto_transition(self):
        self.destroy()
        self.on_next()


# ==========================================
# 配置窗口 (DeepSeek + GUI 双模配置)
# ==========================================
class ConfigWindow(JellyBaseWindow):
    def __init__(self, on_success):
        super().__init__(440, 420, center_on_screen=True)
        self.on_success = on_success
        self.setup_ui()

    def setup_ui(self):
        # 标题
        ctk.CTkLabel(self.bar_frame, text="双引擎配置", font=("Arial", 22, "bold"), text_color=THEME["text_main"]).pack(
            pady=(35, 10))

        # 模型信息展示
        info_frame = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        info_frame.pack(pady=(0, 20))

        gui_model = (os.getenv("GUIAgent_MODEL") or "未配置").split("/")[-1]
        code_model = (os.getenv("CodeAgent_MODEL") or "未配置").split("/")[-1]

        ctk.CTkLabel(info_frame, text=f"👁️ GUI: {gui_model}", font=("Arial", 12), text_color=THEME["text_main"]).pack(
            anchor="w")
        ctk.CTkLabel(info_frame, text=f"🧠 Code: {code_model}", font=("Arial", 12), text_color=THEME["text_main"]).pack(
            anchor="w")
        ctk.CTkLabel(info_frame, text="(Key将同时应用于双引擎)", font=("Arial", 10), text_color=THEME["text_sub"]).pack(
            pady=(5, 0))

        # 输入框
        input_box = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        input_box.pack(fill="x", padx=40)
        ctk.CTkLabel(input_box, text="API Key", font=("Arial", 12, "bold"), text_color=THEME["text_sub"]).pack(
            anchor="w", padx=5)

        self.entry = ctk.CTkEntry(
            input_box, placeholder_text="sk-...", height=44, corner_radius=14,
            border_width=2, border_color="#E5E5EA", fg_color="#FFFFFF",
            font=("Arial", 14), show="•"
        )
        self.entry.pack(fill="x", pady=5)

        self.msg_label = ctk.CTkLabel(self.bar_frame, text="", font=("Arial", 11), text_color=THEME["accent_red"])
        self.msg_label.pack(pady=5)

        # 按钮
        self.btn_save = ctk.CTkButton(
            self.bar_frame, text="激活引擎", width=200, height=48, corner_radius=24,
            fg_color=THEME["accent_blue"], hover_color="#0062CC",
            font=THEME["font_btn"], command=self.save_and_start
        )
        self.btn_save.pack(side="bottom", pady=35)

    def save_and_start(self):
        key = self.entry.get().strip()
        if not key:
            self.msg_label.configure(text="Key 不能为空")
            return

        env_file = dotenv_path if dotenv_path else ".env"
        try:
            # 同时保存 GUIAgent 和 CodeAgent 的 Key
            set_key(env_file, "GUIAgent_API_KEY", key)
            os.environ["GUIAgent_API_KEY"] = key
            set_key(env_file, "CodeAgent_API_KEY", key)
            os.environ["CodeAgent_API_KEY"] = key

            self.destroy()
            self.on_success()
        except Exception as e:
            self.msg_label.configure(text=f"保存失败: {e}")


# ==========================================
# 主控条 (LiquidBar) - 还原原始逻辑 + 历史记录
# ==========================================
class LiquidBar(JellyBaseWindow):
    def __init__(self):
        # [修改] 重构了尺寸和圆角比例，解决"丑丑的棱角"问题
        # 宽度 520, 高度 60 (变窄)
        # padding 5 (减少留白，让条子撑满)
        # corner_radius 25 (高度的一半，50/2 = 25，确保是完美半圆)
        super().__init__(520, 60, center_on_screen=False, top_offset=50, corner_radius=25, padding=5)

        # [新增] 历史管理器
        self.history_manager = HistoryManager()
        self.history_popup = None  # 悬浮窗引用

        # 内部布局
        self.setup_ui()
        self.setup_backend()

        # (拖拽支持已在基类中绑定)

    def setup_ui(self):
        # 布局容器
        layout = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=10, pady=0)

        layout.grid_columnconfigure(1, weight=1)
        layout.grid_rowconfigure(0, weight=1)

        # 1. 状态灯
        self.status = ctk.CTkLabel(layout, text="●", font=("Arial", 28), text_color=THEME["accent_green"], width=30)
        self.status.grid(row=0, column=0, padx=(5, 5))

        # 2. 输入框
        self.entry = ctk.CTkEntry(
            layout,
            placeholder_text="Agent 4 指令...",
            font=THEME["font_entry"],
            fg_color="#FFFFFF",
            border_width=0,
            width=240, # 稍微缩短一点给历史按钮留空间
            height=36, # 高度适配新的条宽
            corner_radius=18
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=(10, 5))
        self.entry.bind("<Return>", self.run_task)

        # 3. [新增] 历史记录按钮
        self.btn_history = ctk.CTkButton(
            layout,
            text="🕒",  # 时钟图标
            width=36,
            height=36,
            corner_radius=18,
            fg_color="#E5E5EA",  # 浅灰底色
            text_color="#000000",
            hover_color="#D1D1D6",
            font=("Arial", 16),
            command=self.toggle_history
        )
        self.btn_history.grid(row=0, column=2, padx=(0, 5))

        # 4. 运行按钮
        self.btn_run = ctk.CTkButton(
            layout,
            text="➤",
            width=36,
            height=36,
            corner_radius=18,
            fg_color=THEME["accent_blue"],
            hover_color="#0062CC",
            font=("Arial", 16),
            command=self.run_task
        )
        self.btn_run.grid(row=0, column=3, padx=(0, 5))

        # 5. 中断按钮 (默认隐藏)
        self.btn_stop = ctk.CTkButton(
            layout,
            text="■",
            width=36,
            height=36,
            corner_radius=18,
            fg_color=THEME["accent_red"],
            hover_color="#D70015",
            font=("Arial", 12),
            command=self.stop_task
        )

    def setup_backend(self):
        self.msg_from_client = queue.Queue()
        self.msg_to_client = queue.Queue()

        self.router = None
        if ROUTER_AVAILABLE:
            try:
                self.router = get_router()
            except:
                self.status.configure(text_color=THEME["accent_red"])

        if VISUALIZER_AVAILABLE:
            visualizer.start()

        self.check_queue()

    # --- [新增] 历史记录逻辑 ---
    def toggle_history(self):
        if self.history_popup and self.history_popup.winfo_exists():
            self.history_popup.destroy()
            self.history_popup = None
            return

        # 获取当前历史
        history_items = self.history_manager.get_all()
        if not history_items:
            return # 没有历史就不弹窗

        # 创建悬浮窗 (Toplevel)
        self.history_popup = ctk.CTkToplevel(self)
        self.history_popup.overrideredirect(True)
        self.history_popup.attributes('-topmost', True)
        self.history_popup.config(background=THEME["transparent_bg_key"])
        self.history_popup.attributes('-transparentcolor', THEME["transparent_bg_key"])

        # 计算位置 (在主条正下方)
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height() - 5 # 紧贴下方
        width = self.winfo_width()
        height = min(len(history_items) * 45 + 30, 300) # 根据条目数量计算高度

        self.history_popup.geometry(f"{width}x{height}+{x}+{y}")

        # 背景容器
        bg = ctk.CTkFrame(
            self.history_popup,
            fg_color=THEME["jelly_bg"],
            corner_radius=20,
            border_width=2,
            border_color=THEME["jelly_border"]
        )
        bg.pack(fill="both", expand=True, padx=15, pady=5)

        # 列表内容
        scroll = ctk.CTkScrollableFrame(bg, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=10)

        for item in history_items:
            # 每个历史条目是一个按钮
            btn = ctk.CTkButton(
                scroll,
                text=item,
                fg_color="transparent",
                text_color=THEME["text_main"],
                hover_color="#E5E5EA",
                anchor="w",
                height=35,
                command=lambda t=item: self.use_history(t)
            )
            btn.pack(fill="x", pady=2)

    def use_history(self, text):
        # 点击历史条目：填充输入框并关闭弹窗
        self.entry.configure(state="normal")
        self.entry.delete(0, 'end')
        self.entry.insert(0, text)
        if self.history_popup:
            self.history_popup.destroy()
            self.history_popup = None

    # --- 逻辑 ---

    def run_task(self, event=None):
        task = self.entry.get().strip()
        if not task: return

        # [新增] 保存到历史记录
        self.history_manager.add(task)
        # 运行前关闭历史弹窗
        if self.history_popup:
            self.history_popup.destroy()

        # UI切换到运行态
        self.btn_run.grid_forget()
        self.btn_stop.grid(row=0, column=3, padx=(0, 5)) # 注意 column 索引变了
        self.status.configure(text_color=THEME["accent_blue"])
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
        self.btn_stop.grid_forget()
        self.btn_run.grid(row=0, column=3, padx=(0, 5)) # 注意 column 索引变了
        self.status.configure(text_color=THEME["accent_green"])
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
                    pass

        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_queue)

    def on_closing(self):
        if VISUALIZER_AVAILABLE:
            visualizer.stop()
        self.destroy()


# ==========================================
# 启动流程控制
# ==========================================
def start_gui_app():
    # 启动主程序
    def launch_main_bar():
        load_dotenv(find_dotenv(), override=True)  # 刷新环境
        app = LiquidBar()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()

    # 启动配置页
    def launch_config():
        win = ConfigWindow(on_success=launch_main_bar)
        win.mainloop()

    # 检查 Key
    key = os.getenv("GUIAgent_API_KEY")

    if not key:
        # 无Key流程：欢迎页 -> 配置页
        welcome = WelcomeWindow(on_next=launch_config)
        welcome.mainloop()
    else:
        # 有Key流程：欢迎页 -> 主程序
        welcome = WelcomeWindow(on_next=launch_main_bar)
        welcome.mainloop()


if __name__ == "__main__":
    start_gui_app()