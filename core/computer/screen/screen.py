import base64
import io

from PIL import Image, ImageGrab


class Screen:
    def __init__(self):
        pass
    def screenshot(self, resize_factor: float = 0.5, format: str= "png", quality: int = 100):
        """
        获取截屏
        :param resize_factor: 缩放因子
        :param format: 格式，可选png/jpeg
        :param quality: 图片质量，jpeg有效
        :return: [{"type": f"image/{format}", "content": base64_encoded}]
        """
        image = ImageGrab.grab()
        new_width = int(image.size[0] * resize_factor)
        new_height = int(image.size[1] * resize_factor)
        image = image.resize((new_width, new_height), Image.LANCZOS)

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

        return [{"type": f"image/{format}", "content": base64_encoded}]