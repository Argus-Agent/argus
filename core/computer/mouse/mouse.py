import pyautogui
import time
from typing import Tuple, Optional, Union


class Mouse:
    """鼠标操作类，提供各种鼠标控制功能"""
    
    def __init__(self):
        """初始化鼠标模块"""
        # 设置PyAutoGUI的安全特性
        pyautogui.FAILSAFE = True  # 移动鼠标到屏幕左上角会触发异常
        pyautogui.PAUSE = 0.1  # 每次操作后暂停0.1秒
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
              clicks: int = 1, interval: float = 0.0, 
              button: str = 'left', duration: float = 0.0) -> dict:
        """
        鼠标点击操作
        
        Args:
            x: X坐标，None表示当前位置
            y: Y坐标，None表示当前位置
            clicks: 点击次数，默认1次
            interval: 多次点击之间的间隔（秒）
            button: 鼠标按键 'left'/'right'/'middle'
            duration: 移动到目标位置的持续时间（秒）
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> mouse.click(100, 200)  # 点击坐标(100, 200)
            >>> mouse.click()  # 点击当前位置
            >>> mouse.click(button='right')  # 右键点击当前位置
        """
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, interval=interval, 
                              button=button, duration=duration)
            else:
                pyautogui.click(clicks=clicks, interval=interval, button=button)
            
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
        """
        鼠标双击操作
        
        Args:
            x: X坐标，None表示当前位置
            y: Y坐标，None表示当前位置
            button: 鼠标按键 'left'/'right'/'middle'
            duration: 移动到目标位置的持续时间（秒）
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> mouse.double_click(300, 400)  # 双击坐标(300, 400)
        """
        return self.click(x, y, clicks=2, button=button, duration=duration)
    
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None,
                    duration: float = 0.0) -> dict:
        """
        鼠标右键点击
        
        Args:
            x: X坐标，None表示当前位置
            y: Y坐标，None表示当前位置
            duration: 移动到目标位置的持续时间（秒）
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> mouse.right_click(500, 300)  # 右键点击坐标(500, 300)
        """
        return self.click(x, y, button='right', duration=duration)
    
    def move(self, x: int, y: int, duration: float = 0.0) -> dict:
        """
        移动鼠标到指定位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动持续时间（秒），0表示立即移动
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> mouse.move(800, 600)  # 立即移动到(800, 600)
            >>> mouse.move(800, 600, duration=1.0)  # 用1秒时间移动到(800, 600)
        """
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
    
    def move_rel(self, x_offset: int, y_offset: int, duration: float = 0.0) -> dict:
        """
        相对移动鼠标（从当前位置偏移）
        
        Args:
            x_offset: X轴偏移量
            y_offset: Y轴偏移量
            duration: 移动持续时间（秒）
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> mouse.move_rel(100, 0)  # 向右移动100像素
        """
        try:
            pyautogui.moveRel(x_offset, y_offset, duration=duration)
            current_pos = pyautogui.position()
            return {
                'success': True,
                'action': 'move_rel',
                'position': (current_pos.x, current_pos.y),
                'offset': (x_offset, y_offset),
                'duration': duration
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'move_rel',
                'error': str(e)
            }
    
    def drag(self, x: int, y: int, duration: float = 1.0, 
             button: str = 'left') -> dict:
        """
        拖拽鼠标到指定位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 拖拽持续时间（秒）
            button: 使用的鼠标按键
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> mouse.drag(500, 500, duration=1.0)  # 拖拽到(500, 500)
        """
        try:
            pyautogui.mouseDown(button=button)
            pyautogui.dragTo(x, y, duration=duration, button=button, mouseDownUp=False)
            time.sleep(0.1)  # 确保拖拽完成
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
    
    def drag_rel(self, x_offset: int, y_offset: int, duration: float = 0.5,
                 button: str = 'left') -> dict:
        """
        相对拖拽（从当前位置偏移）
        
        Args:
            x_offset: X轴偏移量
            y_offset: Y轴偏移量
            duration: 拖拽持续时间（秒）
            button: 使用的鼠标按键
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> mouse.drag_rel(100, 50)  # 向右下拖拽
        """
        try:
            pyautogui.dragRel(x_offset, y_offset, duration=duration, button=button)
            current_pos = pyautogui.position()
            return {
                'success': True,
                'action': 'drag_rel',
                'position': (current_pos.x, current_pos.y),
                'offset': (x_offset, y_offset),
                'button': button,
                'duration': duration
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'drag_rel',
                'error': str(e)
            }
    
    def scroll(self, clicks: int, x: Optional[int] = None, 
               y: Optional[int] = None) -> dict:
        """
        滚动鼠标滚轮
        
        Args:
            clicks: 滚动单位数，正数向上滚动，负数向下滚动
            x: 在指定位置滚动的X坐标（可选）
            y: 在指定位置滚动的Y坐标（可选）
            
        Returns:
            包含操作结果的字典
            
        Examples:
            >>> mouse.scroll(5)  # 向上滚动5个单位
            >>> mouse.scroll(-3)  # 向下滚动3个单位
            >>> mouse.scroll(5, 500, 500)  # 在(500, 500)位置向上滚动
        """
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
    
    def get_position(self) -> dict:
        """
        获取当前鼠标位置
        
        Returns:
            包含鼠标位置的字典
            
        Examples:
            >>> pos = mouse.get_position()
            >>> print(f"鼠标位置: ({pos['x']}, {pos['y']})")
        """
        try:
            pos = pyautogui.position()
            return {
                'success': True,
                'x': pos.x,
                'y': pos.y,
                'position': (pos.x, pos.y)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def mouse_down(self, x: Optional[int] = None, y: Optional[int] = None,
                   button: str = 'left') -> dict:
        """
        按下鼠标按键（不释放）
        
        Args:
            x: X坐标（可选）
            y: Y坐标（可选）
            button: 鼠标按键
            
        Returns:
            包含操作结果的字典
        """
        try:
            if x is not None and y is not None:
                pyautogui.mouseDown(x, y, button=button)
            else:
                pyautogui.mouseDown(button=button)
            
            return {
                'success': True,
                'action': 'mouse_down',
                'button': button
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'mouse_down',
                'error': str(e)
            }
    
    def mouse_up(self, x: Optional[int] = None, y: Optional[int] = None,
                 button: str = 'left') -> dict:
        """
        释放鼠标按键
        
        Args:
            x: X坐标（可选）
            y: Y坐标（可选）
            button: 鼠标按键
            
        Returns:
            包含操作结果的字典
        """
        try:
            if x is not None and y is not None:
                pyautogui.mouseUp(x, y, button=button)
            else:
                pyautogui.mouseUp(button=button)
            
            return {
                'success': True,
                'action': 'mouse_up',
                'button': button
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'mouse_up',
                'error': str(e)
            }


# 创建全局实例，支持直接调用
_mouse_instance = Mouse()

# 导出便捷函数
click = _mouse_instance.click
double_click = _mouse_instance.double_click
right_click = _mouse_instance.right_click
move = _mouse_instance.move
move_rel = _mouse_instance.move_rel
drag = _mouse_instance.drag
drag_rel = _mouse_instance.drag_rel
scroll = _mouse_instance.scroll
get_position = _mouse_instance.get_position
mouse_down = _mouse_instance.mouse_down
mouse_up = _mouse_instance.mouse_up

# Debug
# move(1283,628)
# drag(83,258)