"""
Window Manager - 窗口调整工具
"""

from .manager import (
    WindowManager,
    list_all_windows,
    show_window_info,
    resize,
    move,
    maximize,
    minimize,
    restore,
    activate,
    close
)

from .cli import (
    interactive_menu,
    run_cli
)

__all__ = [
    # 核心类
    'WindowManager',
    
    # 便捷函数
    'list_all_windows',
    'show_window_info',
    'resize',
    'move',
    'maximize',
    'minimize',
    'restore',
    'activate',
    'close',
    
    # CLI功能
    'interactive_menu',
    'run_cli',
]
