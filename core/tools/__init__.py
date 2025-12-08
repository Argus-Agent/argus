"""
工具模块初始化
自动注册所有工具到全局注册中心
"""

from .tools_registry import get_global_registry
from .mouse.mouse import create_mouse_tools
from .keyboard.keyboard import create_keyboard_tools
from .screen.screen import create_screen_tools
from .code.code import create_code_tools
from .window.window import create_window_tools


def initialize_all_tools():
    """
    初始化并注册所有工具到全局注册中心
    
    Returns:
        ToolsRegistry: 全局工具注册中心
        Code: 代码执行器实例
    """
    registry = get_global_registry()
    
    # 注册鼠标工具
    mouse_tools = create_mouse_tools()
    registry.register_multiple(mouse_tools)
    
    # 注册键盘工具
    keyboard_tools = create_keyboard_tools()
    registry.register_multiple(keyboard_tools)
    
    # 注册屏幕工具
    screen_tools = create_screen_tools()
    registry.register_multiple(screen_tools)
    
    # 注册窗口工具
    window_tools = create_window_tools()
    registry.register_multiple(window_tools)
    
    # 注册代码执行工具
    code_tools, code_executor = create_code_tools()
    registry.register_multiple(code_tools)
    
    return registry, code_executor


# 导出注册中心获取函数
__all__ = ['get_global_registry', 'initialize_all_tools']
