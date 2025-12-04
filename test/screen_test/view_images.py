#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看测试生成的截图
"""
import os
import webbrowser
from PIL import Image

def view_screenshots():
    """
    查看生成的截图文件
    """
    print("=== 查看截图文件 ===")
    
    # 查找当前目录下的图片文件
    image_files = []
    for file in os.listdir('.'):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_files.append(file)
    
    if not image_files:
        print("当前目录下没有找到图片文件")
        return
    
    # 按创建时间排序
    image_files.sort(key=lambda x: os.path.getctime(x))
    
    print(f"找到 {len(image_files)} 个图片文件:")
    for i, file in enumerate(image_files, 1):
        try:
            with Image.open(file) as img:
                size_kb = os.path.getsize(file) / 1024
                print(f"{i:2d}. {file}")
                print(f"     尺寸: {img.size[0]}x{img.size[1]}")
                print(f"     大小: {size_kb:.2f} KB")
                print(f"     格式: {img.format}")
                print()
        except Exception as e:
            print(f"{i:2d}. {file} (读取失败: {e})")
    
    # 询问是否打开图片
    try:
        choice = input("输入文件编号打开图片，或按回车退出: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(image_files):
            file_to_open = image_files[int(choice) - 1]
            print(f"正在打开: {file_to_open}")
            # 在默认图片查看器中打开
            if os.name == 'nt':  # Windows
                os.startfile(file_to_open)
            elif os.name == 'posix':  # macOS/Linux
                os.system(f'open "{file_to_open}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{file_to_open}"')
        elif choice:
            print("无效的选择")
    except KeyboardInterrupt:
        print("\n操作取消")
    except Exception as e:
        print(f"打开文件时出错: {e}")

def show_image_grid():
    """
    创建一个图片网格显示
    """
    try:
        from PIL import Image
        
        # 查找测试截图
        test_files = [f for f in os.listdir('.') if f.startswith('test_screenshot_')]
        
        if len(test_files) < 2:
            print("需要至少2个测试截图文件来创建网格")
            return
        
        print("正在创建图片网格...")
        
        # 打开图片
        images = []
        for file in test_files[:4]:  # 最多4张图片
            try:
                img = Image.open(file)
                # 统一调整大小以便显示
                img = img.resize((400, 300), Image.LANCZOS)
                images.append(img)
            except Exception as e:
                print(f"无法加载 {file}: {e}")
        
        if len(images) < 2:
            print("没有足够的有效图片创建网格")
            return
        
        # 创建网格
        cols = 2
        rows = (len(images) + cols - 1) // cols
        
        grid_width = images[0].width * cols
        grid_height = images[0].height * rows
        
        grid = Image.new('RGB', (grid_width, grid_height), 'white')
        
        for i, img in enumerate(images):
            x = (i % cols) * img.width
            y = (i // cols) * img.height
            grid.paste(img, (x, y))
        
        # 保存网格
        grid_file = 'screenshot_grid.png'
        grid.save(grid_file)
        print(f"✓ 图片网格已保存到: {grid_file}")
        
        # 打开网格
        if os.name == 'nt':
            os.startfile(grid_file)
        elif os.name == 'posix':
            os.system(f'open "{grid_file}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{grid_file}"')
        
    except ImportError:
        print("需要PIL库来创建图片网格")
    except Exception as e:
        print(f"创建图片网格时出错: {e}")

if __name__ == "__main__":
    view_screenshots()
    
    # 询问是否创建网格
    try:
        grid_choice = input("\n是否创建图片网格视图？(y/n): ").strip().lower()
        if grid_choice in ['y', 'yes', '是']:
            show_image_grid()
    except KeyboardInterrupt:
        print("\n操作取消")
