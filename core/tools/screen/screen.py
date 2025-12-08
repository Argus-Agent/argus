"""
屏幕工具 - Function Calling格式
包装原有的屏幕截图功能为工具
"""

import base64
import io
import ctypes
from ctypes import windll
from PIL import Image, ImageGrab
from ui_tars import action_parser
from ..base_tool import FunctionTool


def capture_screen_win32():
    """使用Win32 API捕获主屏幕"""
    # Simply capture primary screen
    user32 = windll.user32
    gdi32 = windll.gdi32

    # Get System Metrics for primary screen
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79
    
    # For now, just use GetSystemMetrics modules for primary monitor or full desktop
    # Actually, simpler to just grab the primary monitor which usually starts at 0,0
    width = user32.GetSystemMetrics(0) # SM_CXSCREEN
    height = user32.GetSystemMetrics(1) # SM_CYSCREEN
    x = 0
    y = 0

    hwnd = 0
    hwndDC = user32.GetWindowDC(hwnd)
    mfcDC = gdi32.CreateCompatibleDC(hwndDC)
    saveBitMap = gdi32.CreateCompatibleBitmap(hwndDC, width, height)
    gdi32.SelectObject(mfcDC, saveBitMap)
    
    # Constants
    SRCCOPY = 0x00CC0020
    CAPTUREBLT = 0x40000000

    gdi32.BitBlt(mfcDC, 0, 0, width, height, hwndDC, x, y, SRCCOPY | CAPTUREBLT)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint32),
            ("biWidth", ctypes.c_int32),
            ("biHeight", ctypes.c_int32),
            ("biPlanes", ctypes.c_uint16),
            ("biBitCount", ctypes.c_uint16),
            ("biCompression", ctypes.c_uint32),
            ("biSizeImage", ctypes.c_uint32),
            ("biXPelsPerMeter", ctypes.c_int32),
            ("biYPelsPerMeter", ctypes.c_int32),
            ("biClrUsed", ctypes.c_uint32),
            ("biClrImportant", ctypes.c_uint32)
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0 # BI_RGB

    buffer_len = width * height * 4
    buffer = ctypes.create_string_buffer(buffer_len)
    gdi32.GetDIBits(mfcDC, saveBitMap, 0, height, buffer, ctypes.byref(bmi), 0) # DIB_RGB_COLORS

    image = Image.frombuffer("RGB", (width, height), buffer, "raw", "BGRX", 0, 1)

    gdi32.DeleteObject(saveBitMap)
    gdi32.DeleteDC(mfcDC)
    user32.ReleaseDC(hwnd, hwndDC)

    return image, 0, 0


class Screen:
    """屏幕截图类"""
    
    def __init__(self):
        pass

    def screenshot_base64(
        self, 
        resize_factor: float = None, 
        format: str = "png", 
        quality: int = 100
    ):
        """获取截屏并转换为base64"""
        try:
            image, left, top = capture_screen_win32()
        except Exception as e:
            print(f"[Screen] Win32失败，回退到ImageGrab: {e}")
            image = ImageGrab.grab() # Default grabs all screens or primary
            # Ensure we are consistent if multi-mon support is removed, standard PIL grab might grab all.
            # But "Delete multi-display related code" usually implies simplification.
            left, top = 0, 0

        origin_width = image.size[0]
        origin_height = image.size[1]
        
        if resize_factor is None:
            new_height, new_width = action_parser.smart_resize(origin_height, origin_width)
        else:
            new_width = int(origin_width * resize_factor)
            new_height = int(origin_height * resize_factor)
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        img_byte_arr = io.BytesIO()
        format = format.lower()
        if format == "png":
            image.save(img_byte_arr, format=format)
        elif format == "jpeg":
            image.save(img_byte_arr, format=format, quality=quality)
        else:
            raise ValueError(f"[Screen]不支持的格式: {format}")

        img_bytes = img_byte_arr.getvalue()
        base64_encoded = base64.b64encode(img_bytes).decode('utf-8')

        return {
            "type": f"image/{format}", 
            "content": base64_encoded
        }, origin_width, origin_height, left, top

    def screenshot_pil(self, resize_factor: float = 0.5):
        """获取PIL格式的截屏"""
        try:
            image, left, top = capture_screen_win32()
        except Exception:
            image = ImageGrab.grab()
            left, top = 0, 0
            
        origin_width = image.size[0]
        origin_height = image.size[1]
        
        if resize_factor is None:
            new_height, new_width = action_parser.smart_resize(origin_height, origin_width)
        else:
            new_width = int(image.size[0] * resize_factor)
            new_height = int(image.size[1] * resize_factor)
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return image, origin_width, origin_height, left, top


# 创建全局实例
screen = Screen()


# ===== Function Calling 工具定义 =====

def create_screen_tools():
    """创建所有屏幕工具并返回工具列表"""
    
    tools = []
    
    # Screenshot Tool
    def screenshot_tool_func(resize_factor: float = 0.8, format: str = "png"):
        """截屏工具函数"""
        try:
            result, width, height, left, top = screen.screenshot_base64(
                resize_factor=resize_factor,
                format=format
            )
            return {
                "success": True,
                "image": result,
                "original_width": width,
                "original_height": height,
                "offset_left": left,
                "offset_top": top
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    screenshot_tool = FunctionTool(
        name="screen_screenshot",
        description="捕获屏幕截图。返回base64编码的图片",
        parameters_schema={
            "type": "object",
            "properties": {
                "resize_factor": {
                    "type": "number",
                    "description": "缩放因子，范围0.1-1.0。0.8表示缩放到原尺寸的80%",
                    "default": 0.8,
                    "minimum": 0.1,
                    "maximum": 1.0
                },
                "format": {
                    "type": "string",
                    "enum": ["png", "jpeg"],
                    "description": "图片格式",
                    "default": "png"
                }
            },
            "required": []
        },
        execute_func=screenshot_tool_func
    )
    tools.append(screenshot_tool)
    
    return tools