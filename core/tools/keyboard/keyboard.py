"""
键盘工具 - Function Calling格式
包装原有的pyautogui键盘功能为工具
"""

import pyautogui
import pyperclip
import time
from typing import Optional, List
from ..base_tool import BaseTool, FunctionTool


# 保留原有的Keyboard类用于向后兼容
class Keyboard:
    """键盘操作类，提供各种键盘控制功能"""
    
    def __init__(self):
        """初始化键盘模块"""
        pyautogui.PAUSE = 0.05
    
    def type_text(self, text: str, interval: float = 0.0) -> dict:
        try:
            old_text = pyperclip.paste()
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            pyperclip.copy(old_text)
            time.sleep(interval)
            return {
                'success': True,
                'action': 'type_text',
                'text': text,
                'length': len(text),
                'interval': interval
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'type_text',
                'error': str(e)
            }
    
    def press(self, key: str, presses: int = 1, interval: float = 0.0) -> dict:
        try:
            pyautogui.press(key, presses=presses, interval=interval)
            return {
                'success': True,
                'action': 'press',
                'key': key,
                'presses': presses,
                'interval': interval
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'press',
                'error': str(e)
            }
    
    def hotkey(self, *keys: str) -> dict:
        try:
            pyautogui.hotkey(*keys)
            return {
                'success': True,
                'action': 'hotkey',
                'keys': keys,
                'combination': '+'.join(keys)
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'hotkey',
                'error': str(e)
            }
    
    def key_down(self, key: str) -> dict:
        try:
            pyautogui.keyDown(key)
            return {
                'success': True,
                'action': 'key_down',
                'key': key
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'key_down',
                'error': str(e)
            }
    
    def key_up(self, key: str) -> dict:
        try:
            pyautogui.keyUp(key)
            return {
                'success': True,
                'action': 'key_up',
                'key': key
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'key_up',
                'error': str(e)
            }


# 创建全局实例
_keyboard_instance = Keyboard()

# 向后兼容的直接调用函数
type_text = _keyboard_instance.type_text
press = _keyboard_instance.press
hotkey = _keyboard_instance.hotkey
key_down = _keyboard_instance.key_down
key_up = _keyboard_instance.key_up


# ===== Function Calling 工具定义 =====

def create_keyboard_tools():
    """创建所有键盘工具并返回工具列表"""
    
    tools = []
    
    # 1. Type Text Tool
    type_tool = FunctionTool(
        name="keyboard_type",
        description="输入文本内容。支持中英文混合输入，会使用粘贴方式输入以支持中文",
        parameters_schema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要输入的文本内容"
                },
                "interval": {
                    "type": "number",
                    "description": "输入后的等待时间（秒）",
                    "default": 0.0,
                    "minimum": 0
                }
            },
            "required": ["text"]
        },
        execute_func=lambda **kwargs: _keyboard_instance.type_text(**kwargs)
    )
    tools.append(type_tool)
    
    # 2. Press Key Tool
    press_tool = FunctionTool(
        name="keyboard_press",
        description="按下指定的键。支持字母、数字、功能键(f1-f12)、方向键(up/down/left/right)、特殊键(enter/space/tab/backspace/delete/esc)等",
        parameters_schema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "键名，如 'enter', 'space', 'a', 'f1', 'up' 等"
                },
                "presses": {
                    "type": "integer",
                    "description": "按键次数，默认为1",
                    "default": 1,
                    "minimum": 1
                },
                "interval": {
                    "type": "number",
                    "description": "多次按键之间的间隔（秒）",
                    "default": 0.0,
                    "minimum": 0
                }
            },
            "required": ["key"]
        },
        execute_func=lambda **kwargs: _keyboard_instance.press(**kwargs)
    )
    tools.append(press_tool)
    
    # 3. Hotkey Tool
    hotkey_tool = FunctionTool(
        name="keyboard_hotkey",
        description="按下组合键（快捷键）。例如: Ctrl+C, Ctrl+V, Alt+Tab, Ctrl+Shift+S等",
        parameters_schema={
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "要同时按下的键列表，按顺序传入。例如['ctrl', 'c']表示Ctrl+C",
                    "minItems": 1
                }
            },
            "required": ["keys"]
        },
        execute_func=lambda keys: _keyboard_instance.hotkey(*keys)
    )
    tools.append(hotkey_tool)
    
    # 4. Key Down Tool
    key_down_tool = FunctionTool(
        name="keyboard_key_down",
        description="按下键盘按键（不释放）。通常用于需要长按的场景",
        parameters_schema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "要按下的键名"
                }
            },
            "required": ["key"]
        },
        execute_func=lambda **kwargs: _keyboard_instance.key_down(**kwargs)
    )
    tools.append(key_down_tool)
    
    # 5. Key Up Tool
    key_up_tool = FunctionTool(
        name="keyboard_key_up",
        description="释放键盘按键。与keyboard_key_down配合使用",
        parameters_schema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "要释放的键名"
                }
            },
            "required": ["key"]
        },
        execute_func=lambda **kwargs: _keyboard_instance.key_up(**kwargs)
    )
    tools.append(key_up_tool)
    
    return tools
