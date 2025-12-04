#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screen模块测试文件
测试截图功能并展示图片
"""
import sys
import os
import base64
from io import BytesIO

# 添加core目录到Python路径
core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'core')
if core_path not in sys.path:
    sys.path.insert(0, core_path)

from computer.screen.screen import Screen


def test_screenshot_and_display():
    """
    测试截图功能并展示图片
    """
    print("=== Screen 模块测试开始 ===")
    
    # 创建Screen实例
    screen = Screen()
    
    try:
        # 测试不同参数的截图
        test_cases = [
            {"resize_factor": 0.5, "format": "png", "quality": 100, "name": "PNG格式-50%缩放"},
            {"resize_factor": 1.0, "format": "jpeg", "quality": 95, "name": "JPEG格式-原始大小"},
            {"resize_factor": 0.3, "format": "png", "quality": 100, "name": "PNG格式-30%缩放"},
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- 测试 {i}: {case['name']} ---")
            
            # 调用截图方法
            result = screen.screenshot(
                resize_factor=case["resize_factor"],
                format=case["format"],
                quality=case["quality"]
            )
            
            # 验证结果
            if result and len(result) > 0:
                image_data = result[0]
                print(f"✓ 截图成功")
                print(f"  格式: {image_data['type']}")
                print(f"  Base64长度: {len(image_data['content'])}")
                
                # 保存图片到文件
                save_image_to_file(image_data, f"test_screenshot_{i}.{case['format']}")
                
                # 显示图片信息
                display_image_info(image_data)
            else:
                print("✗ 截图失败")
        
        # 测试错误处理
        print("\n--- 测试错误处理 ---")
        try:
            screen.screenshot(format="unsupported")
            print("✗ 应该抛出错误但没有")
        except ValueError as e:
            print(f"✓ 正确处理了不支持的格式: {e}")
        
        print("\n=== 所有测试完成 ===")
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        return False
    
    return True


def save_image_to_file(image_data, filename):
    """
    将Base64图片数据保存到文件
    """
    try:
        # 解码Base64数据
        image_bytes = base64.b64decode(image_data['content'])
        
        # 保存到文件
        with open(filename, 'wb') as f:
            f.write(image_bytes)
        
        print(f"  ✓ 图片已保存到: {filename}")
        
    except Exception as e:
        print(f"  ✗ 保存图片失败: {e}")


def display_image_info(image_data):
    """
    显示图片信息
    """
    try:
        # 解码Base64数据获取图片信息
        image_bytes = base64.b64decode(image_data['content'])
        
        # 使用PIL读取图片信息
        from PIL import Image
        img = Image.open(BytesIO(image_bytes))
        
        print(f"  图片尺寸: {img.size[0]}x{img.size[1]}")
        print(f"  图片模式: {img.mode}")
        
        # 计算大概的文件大小
        size_kb = len(image_bytes) / 1024
        print(f"  文件大小: {size_kb:.2f} KB")
        
    except Exception as e:
        print(f"  无法获取图片详细信息: {e}")


def interactive_test():
    """
    交互式测试
    """
    print("\n=== 交互式测试 ===")
    print("请输入测试参数（直接回车使用默认值）:")
    
    try:
        resize_factor = input("缩放因子 (0.1-1.0, 默认0.5): ").strip()
        resize_factor = float(resize_factor) if resize_factor else 0.5
        
        format_type = input("图片格式 (png/jpeg, 默认png): ").strip().lower()
        format_type = format_type if format_type else "png"
        
        quality = input("图片质量 (1-100, 仅JPEG有效, 默认95): ").strip()
        quality = int(quality) if quality else 95
        
        print(f"\n正在进行截图...")
        screen = Screen()
        result = screen.screenshot(
            resize_factor=resize_factor,
            format=format_type,
            quality=quality
        )
        
        if result:
            filename = f"interactive_test.{format_type}"
            save_image_to_file(result[0], filename)
            display_image_info(result[0])
            print(f"✓ 交互式测试完成！")
        else:
            print("✗ 交互式测试失败")
            
    except ValueError as e:
        print(f"✗ 输入参数错误: {e}")
    except Exception as e:
        print(f"✗ 交互式测试失败: {e}")


if __name__ == "__main__":
    # 运行基础测试
    success = test_screenshot_and_display()
    
    if success:
        # 询问是否进行交互式测试
        try:
            choice = input("\n是否进行交互式测试？(y/n): ").strip().lower()
            if choice in ['y', 'yes', '是']:
                interactive_test()
        except KeyboardInterrupt:
            print("\n测试被用户中断")
    
    print("\n测试结束。请查看当前目录下保存的截图文件。")
