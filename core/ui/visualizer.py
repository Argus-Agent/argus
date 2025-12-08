"""
✨ Agent4 Vision Overlay - 操作可视化系统
实现点击穿透的全屏绘制层，展示Agent的操作轨迹
"""

import tkinter as tk
import threading
import time
import win32api
import win32con
import win32gui

class ActionVisualizer:
    def __init__(self):
        self.root = None
        self.canvas = None
        self.running = False
        self.width = 0
        self.height = 0
        self._thread = None
        self.lock = threading.Lock()
        
        # 存储要绘制的元素
        self.elements = []  # List of dicts: {'type': 'circle/line', 'coords': ...}

    def start(self):
        if self.running: return
        self.running = True
        self._thread = threading.Thread(target=self._run_ui, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self.root:
            self.root.quit()

    def _run_ui(self):
        self.root = tk.Tk()
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        # 1. 全屏无边框
        self.root.geometry(f"{self.width}x{self.height}+0+0")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        # 2. 背景透明魔法
        # 设置背景色为特定颜色（如纯黑），然后将该颜色设为完全透明
        bg_color = '#000000'
        self.root.configure(bg=bg_color)
        self.root.attributes('-transparentcolor', bg_color)
        
        # 3. 创建画板
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, 
                              bg=bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # 4. 点击穿透 (Click-through) 关键步骤
        # 获取窗口句柄
        hwnd = win32gui.GetParent(self.root.winfo_id())
        # 获取当前样式
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        # 添加穿透属性 (WS_EX_TRANSPARENT) 和 分层属性 (WS_EX_LAYERED)
        style = style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)

        # 启动刷新循环
        self._animate()
        self.root.mainloop()

    def _animate(self):
        if not self.running: return
        
        try:
            self.canvas.delete("all")
            
            with self.lock:
                # 过滤过期的元素
                current_time = time.time()
                self.elements = [el for el in self.elements if current_time - el['start_time'] < el['duration']]
                
                for el in self.elements:
                    life_ratio = (time.time() - el['start_time']) / el['duration']
                    alpha = 1.0 - life_ratio # 渐隐
                    
                    if el['type'] == 'ripple':
                        # 扩散圆圈
                        x, y = el['x'], el['y']
                        max_r = 50
                        r = max_r * life_ratio
                        # Tkinter不支持alpha颜色，只能通过颜色深浅模拟或不模拟
                        # 为了酷炫，我们用鲜艳的颜色
                        color = el.get('color', '#007AFF')
                        width = 4 * (1-life_ratio)
                        if width > 0:
                            self.canvas.create_oval(x-r, y-r, x+r, y+r, outline=color, width=width)
                            
                    elif el['type'] == 'dot':
                        # 实心点
                        x, y = el['x'], el['y']
                        r = 5
                        color = el.get('color', '#34C759')
                        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="")
        
        except Exception:
            pass
            
        self.root.after(20, self._animate)

    # --- 公共API ---
    
    def show_click(self, x, y):
        """显示点击波纹"""
        with self.lock:
            self.elements.append({
                'type': 'ripple',
                'x': x,
                'y': y,
                'start_time': time.time(),
                'duration': 0.8,
                'color': '#00FFFF' # Cyan neon
            })
            self.elements.append({
                'type': 'dot',
                'x': x,
                'y': y,
                'start_time': time.time(),
                'duration': 1.0,
                'color': '#FFFFFF'
            })

    def show_thinking(self, x, y):
        """显示思考位置（可选）"""
        pass

# 全局单例
visualizer = ActionVisualizer()

if __name__ == "__main__":
    # Test
    visualizer.start()
    time.sleep(1)
    print("Clicking...")
    visualizer.show_click(500, 500)
    time.sleep(1)
    visualizer.show_click(800, 600)
    time.sleep(2)
    visualizer.stop()
