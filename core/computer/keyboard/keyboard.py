import pyautogui
import time
from typing import Union, List, Optional


class Keyboard:
    """键盘操作类，提供各种键盘控制功能"""
    
    def __init__(self):
        """初始化键盘模块"""
        pyautogui.PAUSE = 0.05  # 每次操作后暂停0.05秒
    
    def type_text(self, text: str, interval: float = 0.0) -> dict:
        """
        输入文本
        
        Args:
            text: 要输入的文本
            interval: 每个字符之间的间隔时间（秒）
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> keyboard.type_text("Hello World")
            >>> keyboard.type_text("慢速输入", interval=0.1)
            
        Note:
            对于中文输入，需要系统已经切换到中文输入法
        """
        try:
            pyautogui.write(text, interval=interval)
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
        """
        按下指定键
        
        Args:
            key: 键名，如 'enter', 'space', 'a', 'ctrl' 等
            presses: 按键次数
            interval: 多次按键之间的间隔（秒）
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> keyboard.press('enter')  # 按下回车键
            >>> keyboard.press('tab', presses=3)  # 按3次Tab键
            >>> keyboard.press('backspace')  # 按退格键
            
        常用键名:
            - 字母: 'a', 'b', 'c' ...
            - 数字: '0', '1', '2' ...
            - 功能键: 'f1', 'f2' ... 'f12'
            - 方向键: 'up', 'down', 'left', 'right'
            - 特殊键: 'enter', 'space', 'tab', 'backspace', 'delete', 'esc'
            - 修饰键: 'ctrl', 'shift', 'alt', 'win' (或 'command' 在Mac上)
        """
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
        """
        按下组合键（快捷键）
        
        Args:
            *keys: 要同时按下的键，按顺序传入
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> keyboard.hotkey('ctrl', 'c')  # Ctrl+C 复制
            >>> keyboard.hotkey('ctrl', 'v')  # Ctrl+V 粘贴
            >>> keyboard.hotkey('ctrl', 'shift', 's')  # Ctrl+Shift+S
            >>> keyboard.hotkey('alt', 'tab')  # Alt+Tab 切换窗口
            >>> keyboard.hotkey('ctrl', 'a')  # Ctrl+A 全选
        """
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
        """
        按下键（不释放）
        
        Args:
            key: 键名
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> keyboard.key_down('shift')  # 按下Shift键
        """
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
        """
        释放键
        
        Args:
            key: 键名
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> keyboard.key_up('shift')  # 释放Shift键
        """
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
    
    def hold_key(self, key: str, duration: float = 1.0) -> dict:
        """
        按住一个键一段时间
        
        Args:
            key: 键名
            duration: 按住的时间（秒）
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> keyboard.hold_key('space', duration=2.0)  # 按住空格键2秒
        """
        try:
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            return {
                'success': True,
                'action': 'hold_key',
                'key': key,
                'duration': duration
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'hold_key',
                'error': str(e)
            }
    
    # 常用快捷键的便捷方法
    
    def copy(self) -> dict:
        """复制 (Ctrl+C)"""
        return self.hotkey('ctrl', 'c')
    
    def paste(self) -> dict:
        """粘贴 (Ctrl+V)"""
        return self.hotkey('ctrl', 'v')
    
    def cut(self) -> dict:
        """剪切 (Ctrl+X)"""
        return self.hotkey('ctrl', 'x')
    
    def select_all(self) -> dict:
        """全选 (Ctrl+A)"""
        return self.hotkey('ctrl', 'a')
    
    def undo(self) -> dict:
        """撤销 (Ctrl+Z)"""
        return self.hotkey('ctrl', 'z')
    
    def redo(self) -> dict:
        """重做 (Ctrl+Y)"""
        return self.hotkey('ctrl', 'y')
    
    def save(self) -> dict:
        """保存 (Ctrl+S)"""
        return self.hotkey('ctrl', 's')
    
    def find(self) -> dict:
        """查找 (Ctrl+F)"""
        return self.hotkey('ctrl', 'f')
    
    def new_tab(self) -> dict:
        """新建标签页 (Ctrl+T)"""
        return self.hotkey('ctrl', 't')
    
    def close_tab(self) -> dict:
        """关闭标签页 (Ctrl+W)"""
        return self.hotkey('ctrl', 'w')
    
    def refresh(self) -> dict:
        """刷新 (F5)"""
        return self.press('f5')
    
    def switch_window(self) -> dict:
        """切换窗口 (Alt+Tab)"""
        return self.hotkey('alt', 'tab')


# 创建全局实例，支持直接调用
_keyboard_instance = Keyboard()

# 导出便捷函数
type_text = _keyboard_instance.type_text
press = _keyboard_instance.press
hotkey = _keyboard_instance.hotkey
key_down = _keyboard_instance.key_down
key_up = _keyboard_instance.key_up
hold_key = _keyboard_instance.hold_key

# 导出快捷键函数
copy = _keyboard_instance.copy
paste = _keyboard_instance.paste
cut = _keyboard_instance.cut
select_all = _keyboard_instance.select_all
undo = _keyboard_instance.undo
redo = _keyboard_instance.redo
save = _keyboard_instance.save
find = _keyboard_instance.find
new_tab = _keyboard_instance.new_tab
close_tab = _keyboard_instance.close_tab
refresh = _keyboard_instance.refresh
switch_window = _keyboard_instance.switch_window


if __name__ == "__main__":
    # 简单测试
    print("测试键盘模块...")
    
    # 测试按键
    print("按下Esc键...")
    result = press('esc')
    print(f"结果: {result}")
    
    # 测试快捷键
    print("测试Ctrl+C快捷键...")
    result = copy()
    print(f"结果: {result}")
    
    print("键盘模块测试完成！")
