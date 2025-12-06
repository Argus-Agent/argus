"""
Window Manager - 窗口调整工具模块
"""

import sys
from pathlib import Path

# 确保guitools在path中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from guitools import window


class WindowManager:
    """窗口管理器类"""
    
    def __init__(self):
        """初始化窗口管理器"""
        self.window = window
    
    def list_all_windows(self):
        """列出所有窗口"""
        print("\n" + "=" * 60)
        print("所有窗口列表")
        print("=" * 60)
        
        result = self.window.list_windows()
        if result['success'] and result['windows']:
            for i, title in enumerate(result['windows'], 1):
                print(f"{i:2d}. {title}")
            return result['windows']
        else:
            print("未找到窗口")
            return []
    
    def show_window_info(self, title):
        """显示窗口详细信息"""
        result = self.window.get_window_by_title(title)
        if result['success'] and result['found']:
            print("\n" + "=" * 60)
            print("窗口信息")
            print("=" * 60)
            print(f"标题:     {result['title']}")
            print(f"位置:     X={result['left']}, Y={result['top']}")
            print(f"尺寸:     宽={result['width']}, 高={result['height']}")
            print(f"最小化:   {result['is_minimized']}")
            print(f"最大化:   {result['is_maximized']}")
            print(f"活动:     {result['is_active']}")
            return result
        else:
            print(f"\n未找到窗口: {title}")
            return None
    
    def resize(self, title, width=None, height=None):
        """调整窗口大小"""
        info = self.window.get_window_by_title(title)
        if not info or not info.get('found'):
            return {'success': False, 'message': f'未找到窗口: {title}'}
        
        # 如果未提供尺寸，使用当前值
        width = width or info['width']
        height = height or info['height']
        
        return self.window.resize_window(title, width, height)
    
    def move(self, title, x=None, y=None):
        """移动窗口位置"""
        info = self.window.get_window_by_title(title)
        if not info or not info.get('found'):
            return {'success': False, 'message': f'未找到窗口: {title}'}
        
        # 如果未提供坐标，使用当前值
        x = x or info['left']
        y = y or info['top']
        
        return self.window.move_window(title, x, y)
    
    def maximize(self, title):
        """最大化窗口"""
        return self.window.maximize_window(title)
    
    def minimize(self, title):
        """最小化窗口"""
        return self.window.minimize_window(title)
    
    def restore(self, title):
        """恢复窗口"""
        return self.window.restore_window(title)
    
    def activate(self, title):
        """激活窗口"""
        return self.window.activate_window(title)
    
    def close(self, title):
        """关闭窗口"""
        return self.window.close_window(title)


# 创建全局实例
_manager = WindowManager()

# 导出便捷函数
list_all_windows = _manager.list_all_windows
show_window_info = _manager.show_window_info
resize = _manager.resize
move = _manager.move
maximize = _manager.maximize
minimize = _manager.minimize
restore = _manager.restore
activate = _manager.activate
close = _manager.close

