"""
✨ Agent4 Liquid Bar - Apple Jelly Edition
透明、圆角、可视化反馈、果冻动效、历史记录、智能引导、多主题换肤
"""

import sys
import os
import queue
import threading
import json
import webbrowser
import datetime
import tkinter as tk
import customtkinter as ctk
from dotenv import load_dotenv, set_key, find_dotenv

# 1. 环境配置加载
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

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

# ==========================================
# [新增] 主题预设系统
# ==========================================
THEME_PRESETS = {
    "经典果冻": {
        "jelly_bg": "#F5F6FA", "jelly_border": "#FFFFFF",
        "text_main": "#1D1D1F", "text_sub": "#86868B",
        "btn_hover": "#E5E5EA", "entry_bg": "#FFFFFF"
    },
    "暗夜极光": {
        "jelly_bg": "#2C2C2E", "jelly_border": "#3A3A3C",
        "text_main": "#FFFFFF", "text_sub": "#AEAEB2",
        "btn_hover": "#3A3A3C", "entry_bg": "#1C1C1E"
    },
    "樱花布丁": {
        "jelly_bg": "#FFF0F5", "jelly_border": "#FFFFFF",
        "text_main": "#4A232F", "text_sub": "#9C7C85",
        "btn_hover": "#FDE2E8", "entry_bg": "#FFFFFF"
    },
    "薄荷苏打": {
        "jelly_bg": "#F0FFF4", "jelly_border": "#FFFFFF",
        "text_main": "#183D22", "text_sub": "#7A9682",
        "btn_hover": "#DCFCE7", "entry_bg": "#FFFFFF"
    },
    "海盐冰川": {
        "jelly_bg": "#F0F8FF", "jelly_border": "#FFFFFF",
        "text_main": "#1A2F4B", "text_sub": "#7B8CA6",
        "btn_hover": "#E1EFFE", "entry_bg": "#FFFFFF"
    }
}

# 当前使用的主题 (默认经典)
CURRENT_THEME = THEME_PRESETS["经典果冻"].copy()
# 补充通用配置
CURRENT_THEME.update({
    "transparent_bg_key": "#000001",
    "accent_blue": "#007AFF",
    "accent_red": "#FF3B30",
    "accent_green": "#34C759",
    "corner_radius": 32,
    "font_entry": ("PingFang SC", 14),
    "font_btn": ("Arial", 15, "bold")
})


# ==========================================
# 历史记录管理器
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
                    data = json.load(f)
                    if data and isinstance(data[0], str):
                        return [{"text": x, "time": ""} for x in data]
                    return data
            except:
                return []
        return []

    def add(self, text):
        if not text: return
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.history = [item for item in self.history if item['text'] != text]
        self.history.insert(0, {"text": text, "time": time_str})
        if len(self.history) > self.max_items:
            self.history = self.history[:self.max_items]
        self.save()

    def clear(self):
        self.history = []
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
# 基础窗口类
# ==========================================
class JellyBaseWindow(ctk.CTk):
    def __init__(self, width, height, center_on_screen=True, top_offset=None, corner_radius=None, padding=15):
        super().__init__()
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.config(background=CURRENT_THEME["transparent_bg_key"])
        self.attributes('-transparentcolor', CURRENT_THEME["transparent_bg_key"])

        self.target_w = width
        self.target_h = height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        if center_on_screen:
            self.final_x = screen_width // 2 - width // 2
            self.final_y = screen_height // 2 - height // 2
            self.anim_center_x = screen_width // 2
            self.anim_center_y = screen_height // 2
        else:
            fixed_y = top_offset if top_offset is not None else 50
            self.final_x = screen_width // 2 - width // 2
            self.final_y = fixed_y
            self.anim_center_x = self.final_x + (width // 2)
            self.anim_center_y = self.final_y + (height // 2)

        radius = corner_radius if corner_radius is not None else CURRENT_THEME["corner_radius"]

        self.bar_frame = ctk.CTkFrame(
            self,
            fg_color=CURRENT_THEME["jelly_bg"],
            corner_radius=radius,
            bg_color=CURRENT_THEME["transparent_bg_key"],
            border_width=3,
            border_color=CURRENT_THEME["jelly_border"]
        )
        self.bar_frame.pack(fill="both", expand=True, padx=padding, pady=padding)

        # 绑定拖拽到 bar_frame
        self.bar_frame.bind("<Button-1>", self.start_drag)
        self.bar_frame.bind("<B1-Motion>", self.do_drag)

        self.animation_step = 0
        self.after(10, self.animate_pop_in)

    def animate_pop_in(self):
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

    # --- 拖拽逻辑 (全域) ---
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def do_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        new_x = self.winfo_x() + deltax
        new_y = self.winfo_y() + deltay
        self.geometry(f"+{new_x}+{new_y}")
        self.final_x = new_x
        self.final_y = new_y
        self.anim_center_x = new_x + (self.target_w // 2)
        self.anim_center_y = new_y + (self.target_h // 2)


# ==========================================
# 欢迎窗口
# ==========================================
class WelcomeWindow(JellyBaseWindow):
    def __init__(self, on_next):
        super().__init__(300, 350, center_on_screen=True)
        self.on_next = on_next
        self.setup_ui()
        self.after(2500, self.auto_transition)

    def setup_ui(self):
        layout = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        layout.pack(expand=True, fill="both")
        ctk.CTkLabel(layout, text="🍮", font=("Arial", 72)).pack(pady=(45, 10))
        ctk.CTkLabel(layout, text="Agent 4", font=("Arial", 28, "bold"), text_color=CURRENT_THEME["text_main"]).pack(
            pady=(0, 5))
        ctk.CTkLabel(layout, text="欢迎使用", font=("PingFang SC", 18, "bold"),
                     text_color=CURRENT_THEME["accent_blue"]).pack(pady=(5, 0))
        ctk.CTkLabel(layout, text="您的桌面智能协作者", font=("PingFang SC", 12),
                     text_color=CURRENT_THEME["text_sub"]).pack(pady=(5, 0))
        ctk.CTkLabel(layout, text="正在初始化智能引擎...", font=("PingFang SC", 10),
                     text_color=CURRENT_THEME["text_sub"]).pack(side="bottom", pady=25)

    def auto_transition(self):
        self.destroy()
        self.on_next()


# ==========================================
# 指导界面
# ==========================================
class GuideWindow(JellyBaseWindow):
    def __init__(self, on_next):
        super().__init__(500, 520, center_on_screen=True)
        self.on_next = on_next
        self.setup_ui()

    def setup_ui(self):
        header = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header, text="📘", font=("Arial", 28)).pack(side="left")
        ctk.CTkLabel(header, text="快速入门指南", font=("PingFang SC", 20, "bold"),
                     text_color=CURRENT_THEME["text_main"]).pack(side="left", padx=10)

        model_box = ctk.CTkFrame(self.bar_frame, fg_color="#FFFFFF", corner_radius=12, border_width=1,
                                 border_color="#E5E5EA")
        model_box.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(model_box, text="本系统基于火山引擎双模驱动：", font=("Arial", 12, "bold"),
                     text_color="#1D1D1F").pack(anchor="w", padx=15, pady=(10, 5))
        ctk.CTkLabel(model_box, text="🧠 DeepSeek V3 (代码逻辑)", font=("Arial", 11),
                     text_color=CURRENT_THEME["accent_blue"]).pack(anchor="w", padx=25)
        ctk.CTkLabel(model_box, text="👁️ UI-TARS 1.5 (视觉操作)", font=("Arial", 11),
                     text_color=CURRENT_THEME["accent_blue"]).pack(anchor="w", padx=25, pady=(0, 10))

        step_box = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        step_box.pack(fill="x", padx=20, pady=10)
        steps = ["① 点击下方按钮前往火山引擎控制台注册", "② 在「在线推理」中开通服务",
                 "③ 获取 API Key (无需关注接入点ID)"]
        for step in steps:
            ctk.CTkLabel(step_box, text=step, font=("PingFang SC", 12), text_color=CURRENT_THEME["text_main"],
                         anchor="w").pack(fill="x", pady=2)

        def open_url(): webbrowser.open(
            "https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement?LLM=%7B%7D&OpenModelVisible=false")

        self.btn_link = ctk.CTkButton(self.bar_frame, text="🚀 前往火山引擎创建资源", font=("PingFang SC", 13, "bold"),
                                      height=40, corner_radius=20, fg_color="#000000", hover_color="#333333",
                                      command=open_url)
        self.btn_link.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(self.bar_frame, text="完成上述步骤后，即可开始配置", font=("Arial", 11),
                     text_color=CURRENT_THEME["text_sub"]).pack(side="bottom", pady=(0, 20))
        self.btn_next = ctk.CTkButton(self.bar_frame, text="我已准备好，去填 Key ➤", font=("PingFang SC", 14, "bold"),
                                      height=45, corner_radius=22, fg_color=CURRENT_THEME["accent_blue"],
                                      hover_color="#0062CC", command=self.go_next)
        self.btn_next.pack(side="bottom", pady=(10, 5))

    def go_next(self):
        self.destroy()
        if self.on_next: self.on_next()


# ==========================================
# 配置窗口
# ==========================================
class ConfigWindow(JellyBaseWindow):
    def __init__(self, on_success, on_back=None):
        super().__init__(440, 480, center_on_screen=True)
        self.on_success = on_success
        self.on_back = on_back
        self.setup_ui()

    def setup_ui(self):
        if self.on_back:
            self.btn_back = ctk.CTkButton(self.bar_frame, text="← 指南", width=60, height=30, fg_color="transparent",
                                          text_color=CURRENT_THEME["accent_blue"],
                                          hover_color=CURRENT_THEME["btn_hover"], font=("Arial", 13, "bold"),
                                          command=self.go_back)
            self.btn_back.place(x=20, y=20)

        ctk.CTkLabel(self.bar_frame, text="双引擎配置", font=("Arial", 22, "bold"),
                     text_color=CURRENT_THEME["text_main"]).pack(pady=(45, 10))
        info_frame = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        info_frame.pack(pady=(0, 20))

        gui_model = (os.getenv("GUIAgent_MODEL") or "未配置").split("/")[-1]
        code_model = (os.getenv("CodeAgent_MODEL") or "未配置").split("/")[-1]

        ctk.CTkLabel(info_frame, text=f"👁️ GUI: {gui_model}", font=("Arial", 12),
                     text_color=CURRENT_THEME["text_main"]).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"🧠 Code: {code_model}", font=("Arial", 12),
                     text_color=CURRENT_THEME["text_main"]).pack(anchor="w")
        ctk.CTkLabel(info_frame, text="(Key将同时应用于双引擎)", font=("Arial", 10),
                     text_color=CURRENT_THEME["text_sub"]).pack(pady=(5, 0))

        input_box = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        input_box.pack(fill="x", padx=40)
        ctk.CTkLabel(input_box, text="API Key", font=("Arial", 12, "bold"), text_color=CURRENT_THEME["text_sub"]).pack(
            anchor="w", padx=5)
        self.entry = ctk.CTkEntry(input_box, placeholder_text="sk-...", height=44, corner_radius=14, border_width=2,
                                  border_color="#E5E5EA", fg_color=CURRENT_THEME["entry_bg"],
                                  text_color=CURRENT_THEME["text_main"], font=("Arial", 14), show="•")
        self.entry.pack(fill="x", pady=5)

        self.msg_label = ctk.CTkLabel(self.bar_frame, text="", font=("Arial", 11),
                                      text_color=CURRENT_THEME["accent_red"])
        self.msg_label.pack(pady=5)

        self.btn_save = ctk.CTkButton(self.bar_frame, text="激活引擎", width=240, height=50, corner_radius=25,
                                      fg_color=CURRENT_THEME["accent_blue"], hover_color="#0062CC",
                                      font=CURRENT_THEME["font_btn"], command=self.save_and_start)
        self.btn_save.pack(side="bottom", pady=40)

    def go_back(self):
        self.destroy()
        if self.on_back: self.on_back()

    def save_and_start(self):
        key = self.entry.get().strip()
        if not key:
            self.msg_label.configure(text="Key 不能为空")
            return
        env_file = dotenv_path if dotenv_path else ".env"
        try:
            set_key(env_file, "GUIAgent_API_KEY", key)
            os.environ["GUIAgent_API_KEY"] = key
            set_key(env_file, "CodeAgent_API_KEY", key)
            os.environ["CodeAgent_API_KEY"] = key
            self.destroy()
            self.on_success()
        except Exception as e:
            self.msg_label.configure(text=f"保存失败: {e}")


# ==========================================
# 主控条 (含换肤)
# ==========================================
class LiquidBar(JellyBaseWindow):
    def __init__(self):
        super().__init__(540, 60, center_on_screen=False, top_offset=50, corner_radius=25, padding=5)  # 稍微加宽一点给新按钮

        self.history_manager = HistoryManager()
        self.history_popup = None
        self.guide_window = None
        self.theme_popup = None  # 皮肤弹窗

        self.setup_ui()
        self.setup_backend()

    def setup_ui(self):
        self.layout = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        self.layout.pack(fill="both", expand=True, padx=10, pady=0)
        self.layout.grid_columnconfigure(1, weight=1)
        self.layout.grid_rowconfigure(0, weight=1)

        # [拖拽绑定] 必须绑定内部所有非交互组件
        self.layout.bind("<Button-1>", self.start_drag)
        self.layout.bind("<B1-Motion>", self.do_drag)

        self.status = ctk.CTkLabel(self.layout, text="●", font=("Arial", 28), text_color=CURRENT_THEME["accent_green"],
                                   width=30)
        self.status.grid(row=0, column=0, padx=(5, 5))
        self.status.bind("<Button-1>", self.start_drag)
        self.status.bind("<B1-Motion>", self.do_drag)

        self.entry = ctk.CTkEntry(
            self.layout, placeholder_text="Agent 4 指令...", font=CURRENT_THEME["font_entry"],
            fg_color=CURRENT_THEME["entry_bg"], text_color=CURRENT_THEME["text_main"],
            border_width=0, width=180, height=36, corner_radius=18
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=(5, 5))
        self.entry.bind("<Return>", self.run_task)

        # 按钮组：帮助、历史、换肤、运行、停止

        self.btn_help = self.create_icon_btn(self.layout, "❓", self.open_guide)
        self.btn_help.grid(row=0, column=2, padx=2)

        self.btn_history = self.create_icon_btn(self.layout, "🕒", self.toggle_history)
        self.btn_history.grid(row=0, column=3, padx=2)

        # [新增] 换肤按钮
        self.btn_theme = self.create_icon_btn(self.layout, "🎨", self.toggle_theme_picker)
        self.btn_theme.grid(row=0, column=4, padx=2)

        self.btn_run = ctk.CTkButton(
            self.layout, text="➤", width=36, height=36, corner_radius=18,
            fg_color=CURRENT_THEME["accent_blue"], hover_color="#0062CC", font=("Arial", 16),
            command=self.run_task
        )
        self.btn_run.grid(row=0, column=5, padx=(5, 5))

        self.btn_stop = ctk.CTkButton(
            self.layout, text="■", width=36, height=36, corner_radius=18,
            fg_color=CURRENT_THEME["accent_red"], hover_color="#D70015", font=("Arial", 12),
            command=self.stop_task
        )

    def create_icon_btn(self, parent, text, cmd):
        btn = ctk.CTkButton(
            parent, text=text, width=36, height=36, corner_radius=18,
            fg_color="transparent", text_color=CURRENT_THEME["text_main"],
            hover_color=CURRENT_THEME["btn_hover"],
            font=("Arial", 16), command=cmd
        )
        return btn

    # --- 换肤逻辑 ---
    def toggle_theme_picker(self):
        if self.theme_popup and self.theme_popup.winfo_exists():
            self.theme_popup.destroy()
            self.theme_popup = None
            return

        self.theme_popup = ctk.CTkToplevel(self)
        self.theme_popup.overrideredirect(True)
        self.theme_popup.attributes('-topmost', True)
        self.theme_popup.config(background=CURRENT_THEME["transparent_bg_key"])
        self.theme_popup.attributes('-transparentcolor', CURRENT_THEME["transparent_bg_key"])

        x = self.winfo_x() + 200  # 稍微偏右显示
        y = self.winfo_y() + self.winfo_height() - 5
        width = 160
        height = len(THEME_PRESETS) * 40 + 20
        self.theme_popup.geometry(f"{width}x{height}+{x}+{y}")

        bg = ctk.CTkFrame(self.theme_popup, fg_color=CURRENT_THEME["jelly_bg"], corner_radius=16, border_width=2,
                          border_color=CURRENT_THEME["jelly_border"])
        bg.pack(fill="both", expand=True, padx=10, pady=5)

        for name, colors in THEME_PRESETS.items():
            # 小圆点表示颜色
            dot_color = colors["jelly_bg"]
            btn = ctk.CTkButton(
                bg, text=f"  {name}",
                fg_color="transparent", text_color=CURRENT_THEME["text_main"],
                hover_color=CURRENT_THEME["btn_hover"], anchor="w", height=35,
                command=lambda n=name: self.apply_theme(n)
            )
            btn.pack(fill="x", padx=10, pady=2)

    def apply_theme(self, theme_name):
        # 更新全局主题
        global CURRENT_THEME
        new_theme = THEME_PRESETS[theme_name]
        CURRENT_THEME.update(new_theme)

        # 立即更新当前界面颜色
        self.bar_frame.configure(fg_color=CURRENT_THEME["jelly_bg"], border_color=CURRENT_THEME["jelly_border"])
        self.entry.configure(fg_color=CURRENT_THEME["entry_bg"], text_color=CURRENT_THEME["text_main"])

        # 更新按钮颜色
        for btn in [self.btn_help, self.btn_history, self.btn_theme]:
            btn.configure(text_color=CURRENT_THEME["text_main"], hover_color=CURRENT_THEME["btn_hover"])

        # 关闭弹窗
        if self.theme_popup: self.theme_popup.destroy()

    # --- 其他逻辑保持不变 ---
    def setup_backend(self):
        self.msg_from_client = queue.Queue()
        self.msg_to_client = queue.Queue()
        self.router = None
        if ROUTER_AVAILABLE:
            try:
                self.router = get_router()
            except:
                self.status.configure(text_color=CURRENT_THEME["accent_red"])
        if VISUALIZER_AVAILABLE:
            visualizer.start()
        self.check_queue()

    def open_guide(self):
        if self.guide_window and self.guide_window.winfo_exists():
            self.guide_window.focus()
            return
        self.guide_window = GuideWindow(on_next=None)
        self.guide_window.mainloop()

    def toggle_history(self):
        if self.history_popup and self.history_popup.winfo_exists():
            self.history_popup.destroy()
            self.history_popup = None
            return

        history_items = self.history_manager.get_all()
        self.history_popup = ctk.CTkToplevel(self)
        self.history_popup.overrideredirect(True)
        self.history_popup.attributes('-topmost', True)
        self.history_popup.config(background=CURRENT_THEME["transparent_bg_key"])
        self.history_popup.attributes('-transparentcolor', CURRENT_THEME["transparent_bg_key"])

        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height() - 5
        width = self.winfo_width()
        item_count = len(history_items)
        height = min(item_count * 40 + 70, 320)
        if item_count == 0: height = 70

        self.history_popup.geometry(f"{width}x{height}+{x}+{y}")

        bg = ctk.CTkFrame(self.history_popup, fg_color=CURRENT_THEME["jelly_bg"], corner_radius=20, border_width=2,
                          border_color=CURRENT_THEME["jelly_border"])
        bg.pack(fill="both", expand=True, padx=15, pady=5)

        btn_clear = ctk.CTkButton(bg, text="🗑️ 清空历史", width=100, height=28, fg_color="transparent",
                                  text_color=CURRENT_THEME["accent_red"], hover_color=CURRENT_THEME["btn_hover"],
                                  font=("Arial", 12), command=self.clear_history)
        btn_clear.pack(side="bottom", pady=10)

        scroll = ctk.CTkScrollableFrame(bg, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=(10, 5))

        for item in history_items:
            time_str = item.get('time', '')
            text_str = item.get('text', '')
            display_text = f"[{time_str}] {text_str}" if time_str else text_str
            btn = ctk.CTkButton(scroll, text=display_text, fg_color="transparent",
                                text_color=CURRENT_THEME["text_main"], hover_color=CURRENT_THEME["btn_hover"],
                                anchor="w", height=32, command=lambda t=text_str: self.use_history(t))
            btn.pack(fill="x", pady=1)

    def use_history(self, text):
        self.entry.configure(state="normal")
        self.entry.delete(0, 'end')
        self.entry.insert(0, text)
        if self.history_popup:
            self.history_popup.destroy()
            self.history_popup = None

    def clear_history(self):
        self.history_manager.clear()
        if self.history_popup:
            self.history_popup.destroy()
            self.history_popup = None

    def run_task(self, event=None):
        task = self.entry.get().strip()
        if not task: return
        self.history_manager.add(task)
        if self.history_popup: self.history_popup.destroy()

        self.btn_run.grid_forget()
        self.btn_stop.grid(row=0, column=5, padx=(5, 5))
        self.status.configure(text_color=CURRENT_THEME["accent_blue"])
        self.entry.configure(state="disabled", fg_color="#E5E5E5")
        threading.Thread(target=self._run_thread, args=(task,), daemon=True).start()

    def stop_task(self):
        self.msg_from_client.put({"name": "User", "type": "request", "content": "stop_agent"})
        self.reset_ui()

    def _run_thread(self, task):
        if self.router:
            self.router.execute_with_fallback(task, self.msg_from_client, self.msg_to_client)

    def reset_ui(self):
        self.btn_stop.grid_forget()
        self.btn_run.grid(row=0, column=5, padx=(5, 5))
        self.status.configure(text_color=CURRENT_THEME["accent_green"])
        self.entry.configure(state="normal", fg_color=CURRENT_THEME["entry_bg"])

    def check_queue(self):
        try:
            while True:
                msg = self.msg_to_client.get_nowait()
                mtype = msg.get('type')
                content = msg.get('content')
                if mtype == "status":
                    if content == "[STOP]": self.reset_ui()
                elif mtype == "action_point":
                    if VISUALIZER_AVAILABLE and isinstance(content, dict):
                        visualizer.show_click(content.get('x'), content.get('y'))
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_queue)

    def on_closing(self):
        if VISUALIZER_AVAILABLE: visualizer.stop()
        self.destroy()


# ==========================================
# 启动流程
# ==========================================
def start_gui_app():
    def launch_main_bar():
        load_dotenv(find_dotenv(), override=True)
        app = LiquidBar()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()

    def launch_config():
        win = ConfigWindow(on_success=launch_main_bar, on_back=launch_guide)
        win.mainloop()

    def launch_guide():
        guide = GuideWindow(on_next=launch_config)
        guide.mainloop()

    key = os.getenv("GUIAgent_API_KEY")

    if not key:
        welcome = WelcomeWindow(on_next=launch_guide)
        welcome.mainloop()
    else:
        welcome = WelcomeWindow(on_next=launch_main_bar)
        welcome.mainloop()


if __name__ == "__main__":
    start_gui_app()