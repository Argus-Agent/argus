import base64
import io
import ctypes
from ctypes import windll, byref, sizeof, c_void_p
from PIL import Image, ImageGrab
from ui_tars import action_parser

def capture_screen_win32():
    # Constants
    SM_CXSCREEN = 0
    SM_CYSCREEN = 1
    SRCCOPY = 0x00CC0020
    CAPTUREBLT = 0x40000000
    DIB_RGB_COLORS = 0
    BI_RGB = 0

    # Get screen dimensions
    user32 = windll.user32
    gdi32 = windll.gdi32
    width = user32.GetSystemMetrics(SM_CXSCREEN)
    height = user32.GetSystemMetrics(SM_CYSCREEN)

    # Create DC
    hwnd = 0  # Desktop
    hwndDC = user32.GetWindowDC(hwnd)
    mfcDC = gdi32.CreateCompatibleDC(hwndDC)
    saveBitMap = gdi32.CreateCompatibleBitmap(hwndDC, width, height)
    gdi32.SelectObject(mfcDC, saveBitMap)

    # BitBlt with CAPTUREBLT to capture layered windows (like context menus)
    gdi32.BitBlt(mfcDC, 0, 0, width, height, hwndDC, 0, 0, SRCCOPY | CAPTUREBLT)

    # Bitmap Info Header
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", ctypes.c_uint32),
                    ("biWidth", ctypes.c_int32),
                    ("biHeight", ctypes.c_int32),
                    ("biPlanes", ctypes.c_uint16),
                    ("biBitCount", ctypes.c_uint16),
                    ("biCompression", ctypes.c_uint32),
                    ("biSizeImage", ctypes.c_uint32),
                    ("biXPelsPerMeter", ctypes.c_int32),
                    ("biYPelsPerMeter", ctypes.c_int32),
                    ("biClrUsed", ctypes.c_uint32),
                    ("biClrImportant", ctypes.c_uint32)]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height  # Top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = BI_RGB

    # Get bits
    buffer_len = width * height * 4
    buffer = ctypes.create_string_buffer(buffer_len)
    gdi32.GetDIBits(mfcDC, saveBitMap, 0, height, buffer, ctypes.byref(bmi), DIB_RGB_COLORS)

    # Create PIL Image (BGRX -> RGB)
    image = Image.frombuffer("RGB", (width, height), buffer, "raw", "BGRX", 0, 1)

    # Cleanup
    gdi32.DeleteObject(saveBitMap)
    gdi32.DeleteDC(mfcDC)
    user32.ReleaseDC(hwnd, hwndDC)

    return image

class Screen:
    def __init__(self):
        pass
    def screenshot_base64(self, resize_factor: float = None, format: str= "png", quality: int = 100):
        """
        获取截屏
        :param resize_factor: 缩放因子，默认为None就调用smart_resize来缩放好传输给qwen25vl
        :param format: 格式，可选png/jpeg
        :param quality: 图片质量，jpeg有效
        :return: [{"type": f"image/{format}", "content": base64_encoded}], origin_width, origin_height
        """
        try:
            image = capture_screen_win32()
        except Exception as e:
            print(f"[Screen] Win32 capture failed, falling back to ImageGrab: {e}")
            image = ImageGrab.grab(include_layered_windows=True) if hasattr(ImageGrab, 'grab') and 'include_layered_windows' in ImageGrab.grab.__code__.co_varnames else ImageGrab.grab()

        # 缩放
        origin_width = image.size[0]
        origin_height = image.size[1]
        if resize_factor is None:
            new_height, new_width = action_parser.smart_resize(origin_height, origin_width)
            print("original size", image.size, (origin_width, origin_height))
            print("resize to", (new_width, new_height))
        else:
            new_width = int(origin_width * resize_factor)
            new_height = int(origin_height * resize_factor)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        img_byte_arr= io.BytesIO()
        format = format.lower()
        if format == "png":
            image.save(img_byte_arr, format=format)
        elif format == "jpeg":
            image.save(img_byte_arr, format=format, quality=quality)
        else:
            raise ValueError("[Screen]Unsupported format: ", format)

        img_bytes = img_byte_arr.getvalue()
        base64_encoded = base64.b64encode(img_bytes).decode('utf-8')

        return {"type": f"image/{format}", "content": base64_encoded}, origin_width, origin_height

    def screenshhot_pil(self, resize_factor: float = 0.5):
        """
        获取截屏并返回PIL图像对象
        :param resize_factor: 缩放因子
        :return: PIL Image对象, origin_width, origin_height
        """
        try:
            image = capture_screen_win32()
        except Exception:
            image = ImageGrab.grab()
            
        # 缩放
        origin_width = image.size[0]
        origin_height = image.size[1]
        if resize_factor is None:
            new_height, new_width = action_parser.smart_resize(origin_height, origin_width)
            print("original size", image.size)
            print("resize to", (new_width, new_height))
        else:
            new_width = int(image.size[0] * resize_factor)
            new_height = int(image.size[1] * resize_factor)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return image, origin_width, origin_height

screen = Screen()
screen.screenshot_base64()
# print(screen.screenshot_base64())