"""
窗口管理工具 - Function Calling格式
提供窗口列表、查找、调整大小、移动、最大化最小化等功能
"""

import sys
import logging
from typing import List, Dict, Any, Optional
from ..base_tool import FunctionTool

# Windows平台特定导入
try:
    if sys.platform == 'win32':
        import win32gui
        import win32con
        import win32process
        WIN32_AVAILABLE = True
    else:
        WIN32_AVAILABLE = False
except ImportError:
    WIN32_AVAILABLE = False
    logging.warning("win32gui未安装，窗口管理功能将受限")


class WindowManager:
    """窗口管理器类"""
    
    def __init__(self):
        """初始化窗口管理器"""
        if not WIN32_AVAILABLE:
            raise RuntimeError("窗口管理需要pywin32库（仅Windows）")
    
    def list_windows(self) -> Dict[str, Any]:
        """列出所有可见窗口"""
        try:
            windows = []
            
            def enum_windows_callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:  # 只包含有标题的窗口
                        windows.append({
                            'hwnd': hwnd,
                            'title': title
                        })
                return True
            
            win32gui.EnumWindows(enum_windows_callback, None)
            
            return {
                'success': True,
                'windows': [w['title'] for w in windows],
                'count': len(windows)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def find_window_by_title(self, title: str, exact: bool = False) -> Optional[int]:
        """根据标题查找窗口句柄"""
        try:
            if exact:
                hwnd = win32gui.FindWindow(None, title)
                return hwnd if hwnd else None
            else:
                # 模糊匹配
                found_hwnd = None
                title_lower = title.lower()
                
                def enum_callback(hwnd, _):
                    nonlocal found_hwnd
                    if win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if title_lower in window_title.lower():
                            found_hwnd = hwnd
                            return False  # 停止枚举
                    return True
                
                win32gui.EnumWindows(enum_callback, None)
                return found_hwnd
        except Exception as e:
            logging.error(f"查找窗口失败: {e}")
            return None
    
    def get_window_info(self, title: str) -> Dict[str, Any]:
        """获取窗口详细信息"""
        try:
            hwnd = self.find_window_by_title(title)
            if not hwnd:
                return {
                    'success': False,
                    'found': False,
                    'message': f'未找到窗口: {title}'
                }
            
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            
            placement = win32gui.GetWindowPlacement(hwnd)
            is_minimized = (placement[1] == win32con.SW_SHOWMINIMIZED)
            is_maximized = (placement[1] == win32con.SW_SHOWMAXIMIZED)
            is_active = (win32gui.GetForegroundWindow() == hwnd)
            
            return {
                'success': True,
                'found': True,
                'hwnd': hwnd,
                'title': win32gui.GetWindowText(hwnd),
                'left': left,
                'top': top,
                'width': right - left,
                'height': bottom - top,
                'is_minimized': is_minimized,
                'is_maximized': is_maximized,
                'is_active': is_active
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def resize_window(self, title: str, width: int, height: int) -> Dict[str, Any]:
        """调整窗口大小"""
        try:
            hwnd = self.find_window_by_title(title)
            if not hwnd:
                return {'success': False, 'message': f'未找到窗口: {title}'}
            
            rect = win32gui.GetWindowRect(hwnd)
            left, top = rect[0], rect[1]
            
            win32gui.SetWindowPos(
                hwnd, 
                win32con.HWND_TOP, 
                left, top, width, height,
                win32con.SWP_SHOWWINDOW
            )
            
            return {
                'success': True,
                'action': 'resize',
                'width': width,
                'height': height
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def move_window(self, title: str, x: int, y: int) -> Dict[str, Any]:
        """移动窗口位置"""
        try:
            hwnd = self.find_window_by_title(title)
            if not hwnd:
                return {'success': False, 'message': f'未找到窗口: {title}'}
            
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            win32gui.SetWindowPos(
                hwnd, 
                win32con.HWND_TOP, 
                x, y, width, height,
                win32con.SWP_SHOWWINDOW
            )
            
            return {
                'success': True,
                'action': 'move',
                'x': x,
                'y': y
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def maximize_window(self, title: str) -> Dict[str, Any]:
        """最大化窗口"""
        try:
            hwnd = self.find_window_by_title(title)
            if not hwnd:
                return {'success': False, 'message': f'未找到窗口: {title}'}
            
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            
            return {
                'success': True,
                'action': 'maximize'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def minimize_window(self, title: str) -> Dict[str, Any]:
        """最小化窗口"""
        try:
            hwnd = self.find_window_by_title(title)
            if not hwnd:
                return {'success': False, 'message': f'未找到窗口: {title}'}
            
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            
            return {
                'success': True,
                'action': 'minimize'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def restore_window(self, title: str) -> Dict[str, Any]:
        """恢复窗口（从最大化或最小化状态）"""
        try:
            hwnd = self.find_window_by_title(title)
            if not hwnd:
                return {'success': False, 'message': f'未找到窗口: {title}'}
            
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            return {
                'success': True,
                'action': 'restore'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def activate_window(self, title: str) -> Dict[str, Any]:
        """激活窗口（置于前台）"""
        try:
            hwnd = self.find_window_by_title(title)
            if not hwnd:
                return {'success': False, 'message': f'未找到窗口: {title}'}
            
            # 先显示窗口（如果最小化）
            placement = win32gui.GetWindowPlacement(hwnd)
            if placement[1] == win32con.SW_SHOWMINIMIZED:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 设为前台窗口
            win32gui.SetForegroundWindow(hwnd)
            
            return {
                'success': True,
                'action': 'activate'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def close_window(self, title: str) -> Dict[str, Any]:
        """关闭窗口"""
        try:
            hwnd = self.find_window_by_title(title)
            if not hwnd:
                return {'success': False, 'message': f'未找到窗口: {title}'}
            
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            
            return {
                'success': True,
                'action': 'close'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }


# 创建全局实例
try:
    _window_manager = WindowManager()
except RuntimeError:
    _window_manager = None
    logging.warning("窗口管理器初始化失败，功能不可用")


# 向后兼容的直接调用函数
def list_windows():
    """列出所有窗口"""
    if _window_manager:
        return _window_manager.list_windows()
    return {'success': False, 'error': 'WindowManager未初始化'}

def get_window_info(title: str):
    """获取窗口信息"""
    if _window_manager:
        return _window_manager.get_window_info(title)
    return {'success': False, 'error': 'WindowManager未初始化'}

def resize(title: str, width: int, height: int):
    """调整窗口大小"""
    if _window_manager:
        return _window_manager.resize_window(title, width, height)
    return {'success': False, 'error': 'WindowManager未初始化'}

def move(title: str, x: int, y: int):
    """移动窗口"""
    if _window_manager:
        return _window_manager.move_window(title, x, y)
    return {'success': False, 'error': 'WindowManager未初始化'}

def maximize(title: str):
    """最大化窗口"""
    if _window_manager:
        return _window_manager.maximize_window(title)
    return {'success': False, 'error': 'WindowManager未初始化'}

def minimize(title: str):
    """最小化窗口"""
    if _window_manager:
        return _window_manager.minimize_window(title)
    return {'success': False, 'error': 'WindowManager未初始化'}

def restore(title: str):
    """恢复窗口"""
    if _window_manager:
        return _window_manager.restore_window(title)
    return {'success': False, 'error': 'WindowManager未初始化'}

def activate(title: str):
    """激活窗口"""
    if _window_manager:
        return _window_manager.activate_window(title)
    return {'success': False, 'error': 'WindowManager未初始化'}

def close_window(title: str):
    """关闭窗口"""
    if _window_manager:
        return _window_manager.close_window(title)
    return {'success': False, 'error': 'WindowManager未初始化'}


# ===== Function Calling 工具定义 =====

def create_window_tools():
    """创建所有窗口管理工具并返回工具列表"""
    
    if not _window_manager:
        logging.warning("窗口管理器不可用，跳过工具创建")
        return []
    
    tools = []
    
    # 1. List Windows Tool
    list_tool = FunctionTool(
        name="window_list",
        description="列出所有可见的窗口标题",
        parameters_schema={
            "type": "object",
            "properties": {},
            "required": []
        },
        execute_func=lambda: _window_manager.list_windows()
    )
    tools.append(list_tool)
    
    # 2. Get Window Info Tool
    info_tool = FunctionTool(
        name="window_get_info",
        description="获取指定窗口的详细信息（位置、大小、状态等）",
        parameters_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "窗口标题（支持模糊匹配）"
                }
            },
            "required": ["title"]
        },
        execute_func=lambda title: _window_manager.get_window_info(title)
    )
    tools.append(info_tool)
    
    # 3. Resize Window Tool
    resize_tool = FunctionTool(
        name="window_resize",
        description="调整窗口大小",
        parameters_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "窗口标题"
                },
                "width": {
                    "type": "integer",
                    "description": "新宽度（像素）",
                    "minimum": 100
                },
                "height": {
                    "type": "integer",
                    "description": "新高度（像素）",
                    "minimum": 100
                }
            },
            "required": ["title", "width", "height"]
        },
        execute_func=lambda title, width, height: _window_manager.resize_window(title, width, height)
    )
    tools.append(resize_tool)
    
    # 4. Move Window Tool
    move_tool = FunctionTool(
        name="window_move",
        description="移动窗口到指定位置",
        parameters_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "窗口标题"
                },
                "x": {
                    "type": "integer",
                    "description": "X坐标（像素）"
                },
                "y": {
                    "type": "integer",
                    "description": "Y坐标（像素）"
                }
            },
            "required": ["title", "x", "y"]
        },
        execute_func=lambda title, x, y: _window_manager.move_window(title, x, y)
    )
    tools.append(move_tool)
    
    # 5. Maximize Window Tool
    maximize_tool = FunctionTool(
        name="window_maximize",
        description="最大化窗口",
        parameters_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "窗口标题"
                }
            },
            "required": ["title"]
        },
        execute_func=lambda title: _window_manager.maximize_window(title)
    )
    tools.append(maximize_tool)
    
    # 6. Minimize Window Tool
    minimize_tool = FunctionTool(
        name="window_minimize",
        description="最小化窗口",
        parameters_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "窗口标题"
                }
            },
            "required": ["title"]
        },
        execute_func=lambda title: _window_manager.minimize_window(title)
    )
    tools.append(minimize_tool)
    
    # 7. Restore Window Tool
    restore_tool = FunctionTool(
        name="window_restore",
        description="恢复窗口到正常大小（从最大化或最小化状态）",
        parameters_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "窗口标题"
                }
            },
            "required": ["title"]
        },
        execute_func=lambda title: _window_manager.restore_window(title)
    )
    tools.append(restore_tool)
    
    # 8. Activate Window Tool
    activate_tool = FunctionTool(
        name="window_activate",
        description="激活窗口（置于前台并获得焦点）",
        parameters_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "窗口标题"
                }
            },
            "required": ["title"]
        },
        execute_func=lambda title: _window_manager.activate_window(title)
    )
    tools.append(activate_tool)
    
    # 9. Close Window Tool
    close_tool = FunctionTool(
        name="window_close",
        description="关闭窗口",
        parameters_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "窗口标题"
                }
            },
            "required": ["title"]
        },
        execute_func=lambda title: _window_manager.close_window(title)
    )
    tools.append(close_tool)
    
    return tools
