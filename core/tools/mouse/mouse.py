"""
鼠标工具 - Function Calling格式
包装原有的pyautogui鼠标功能为工具
"""

import pyautogui
import time
from typing import Optional
from ..base_tool import BaseTool, FunctionTool


# 保留原有的Mouse类用于向后兼容
class Mouse:
    """鼠标操作类，提供各种鼠标控制功能"""
    
    def __init__(self):
        """初始化鼠标模块"""
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
              clicks: int = 1, interval: float = 0.0, 
              button: str = 'left', duration: float = 0.0) -> dict:
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, interval=interval, 
                              button=button, duration=duration)
            else:
                pyautogui.click(clicks=clicks, interval= interval, button=button)
            
            current_pos = pyautogui.position()
            return {
                'success': True,
                'action': 'click',
                'position': (current_pos.x, current_pos.y),
                'button': button,
                'clicks': clicks
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'click',
                'error': str(e)
            }
    
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None,
                     button: str = 'left', duration: float = 0.0) -> dict:
        return self.click(x, y, clicks=2, button=button, duration=duration)
    
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None,
                    duration: float = 0.0) -> dict:
        return self.click(x, y, button='right', duration=duration)
    
    def move(self, x: int, y: int, duration: float = 0.0) -> dict:
        try:
            pyautogui.moveTo(x, y, duration=duration)
            current_pos = pyautogui.position()
            return {
                'success': True,
                'action': 'move',
                'position': (current_pos.x, current_pos.y),
                'duration': duration
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'move',
                'error': str(e)
            }
    
    def drag(self, x: int, y: int, duration: float = 1.0, 
             button: str = 'left') -> dict:
        try:
            pyautogui.mouseDown(button=button)
            pyautogui.dragTo(x, y, duration=duration, button=button, mouseDownUp=False)
            time.sleep(0.1)
            pyautogui.mouseUp(button=button)
            current_pos = pyautogui.position()
            return {
                'success': True,
                'action': 'drag',
                'position': (current_pos.x, current_pos.y),
                'button': button,
                'duration': duration
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'drag',
                'error': str(e)
            }
    
    def scroll(self, clicks: int, x: Optional[int] = None, 
               y: Optional[int] = None) -> dict:
        try:
            if x is not None and y is not None:
                pyautogui.scroll(clicks, x, y)
            else:
                pyautogui.scroll(clicks)
            
            return {
                'success': True,
                'action': 'scroll',
                'clicks': clicks,
                'position': (x, y) if x and y else 'current'
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'scroll',
                'error': str(e)
            }


# 创建全局实例
_mouse_instance = Mouse()

# 向后兼容的直接调用函数
click = _mouse_instance.click
double_click = _mouse_instance.double_click
right_click = _mouse_instance.right_click
move = _mouse_instance.move
drag = _mouse_instance.drag
scroll = _mouse_instance.scroll


# ===== Function Calling 工具定义 =====

def create_mouse_tools():
    """创建所有鼠标工具并返回工具列表"""
    
    tools = []
    
    # 1. Mouse Click Tool
    click_tool = FunctionTool(
        name="mouse_click",
        description="在指定位置点击鼠标。如果不提供坐标则在当前位置点击",
        parameters_schema={
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer",
                    "description": "X坐标（像素）"
                },
                "y": {
                    "type": "integer",
                    "description": "Y坐标（像素）"
                },
                "button": {
                    "type": "string",
                    "enum": ["left", "right", "middle"],
                    "description": "鼠标按键，默认为left",
                    "default": "left"
                },
                "clicks": {
                    "type": "integer",
                    "description": "点击次数，默认为1",
                    "default": 1,
                    "minimum": 1
                }
            },
            "required": []
        },
        execute_func=lambda **kwargs: _mouse_instance.click(**kwargs)
    )
    tools.append(click_tool)
    
    # 2. Mouse Double Click Tool
    double_click_tool = FunctionTool(
        name="mouse_double_click",
        description="在指定位置双击鼠标",
        parameters_schema={
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer",
                    "description": "X坐标（像素）"
                },
                "y": {
                    "type": "integer",
                    "description": "Y坐标（像素）"
                }
            },
            "required": ["x", "y"]
        },
        execute_func=lambda **kwargs: _mouse_instance.double_click(**kwargs)
    )
    tools.append(double_click_tool)
    
    # 3. Mouse Right Click Tool
    right_click_tool = FunctionTool(
        name="mouse_right_click",
        description="在指定位置右键点击鼠标",
        parameters_schema={
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer",
                    "description": "X坐标（像素）"
                },
                "y": {
                    "type": "integer",
                    "description": "Y坐标（像素）"
                }
            },
            "required": ["x", "y"]
        },
        execute_func=lambda **kwargs: _mouse_instance.right_click(**kwargs)
    )
    tools.append(right_click_tool)
    
    # 4. Mouse Move Tool
    move_tool = FunctionTool(
        name="mouse_move",
        description="移动鼠标到指定位置",
        parameters_schema={
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer",
                    "description": "目标X坐标（像素）"
                },
                "y": {
                    "type": "integer",
                    "description": "目标Y坐标（像素）"
                },
                "duration": {
                    "type": "number",
                    "description": "移动持续时间（秒），0表示立即移动",
                    "default": 0.0,
                    "minimum": 0
                }
            },
            "required": ["x", "y"]
        },
        execute_func=lambda **kwargs: _mouse_instance.move(**kwargs)
    )
    tools.append(move_tool)
    
    # 5. Mouse Drag Tool
    drag_tool = FunctionTool(
        name="mouse_drag",
        description="拖拽鼠标到指定位置（从当前位置按住鼠标拖动到目标位置）",
        parameters_schema={
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer",
                    "description": "目标X坐标（像素）"
                },
                "y": {
                    "type": "integer",
                    "description": "目标Y坐标（像素）"
                },
                "duration": {
                    "type": "number",
                    "description": "拖拽持续时间（秒）",
                    "default": 1.0,
                    "minimum": 0
                },
                "button": {
                    "type": "string",
                    "enum": ["left", "right", "middle"],
                    "description": "使用的鼠标按键",
                    "default": "left"
                }
            },
            "required": ["x", "y"]
        },
        execute_func=lambda **kwargs: _mouse_instance.drag(**kwargs)
    )
    tools.append(drag_tool)
    
    # 6. Mouse Scroll Tool
    scroll_tool = FunctionTool(
        name="mouse_scroll",
        description="滚动鼠标滚轮。正数向上滚动，负数向下滚动",
        parameters_schema={
            "type": "object",
            "properties": {
                "clicks": {
                    "type": "integer",
                    "description": "滚动单位数。正数向上，负数向下"
                },
                "x": {
                    "type": "integer",
                    "description": "在指定位置滚动的X坐标（可选）"
                },
                "y": {
                    "type": "integer",
                    "description": "在指定位置滚动的Y坐标（可选）"
                }
            },
            "required": ["clicks"]
        },
        execute_func=lambda **kwargs: _mouse_instance.scroll(**kwargs)
    )
    tools.append(scroll_tool)
    
    return tools