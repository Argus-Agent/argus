#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screen测试快速开始脚本
一键运行测试并查看结果
"""
import os
import sys
import subprocess

def main():
    """
    主流程：运行测试 -> 查看结果
    """
    print("=== Screen 模块测试快速开始 ===\n")
    
    # 1. 运行快速测试
    print("1. 正在运行测试...")
    try:
        result = subprocess.run([sys.executable, 'run_test.py'], 
                              capture_output=True, text=True, cwd='.')
        print(result.stdout)
        if result.stderr:
            print("错误信息:", result.stderr)
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return
    
    # 2. 检查生成的文件
    print("\n2. 检查生成的文件...")
    image_files = [f for f in os.listdir('.') 
                  if f.startswith('test_screenshot_') and 
                  f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        print("❌ 没有找到生成的截图文件")
        return
    
    print(f"✓ 生成了 {len(image_files)} 个截图文件:")
    for file in image_files:
        size_kb = os.path.getsize(file) / 1024
        print(f"  - {file} ({size_kb:.1f} KB)")
    
    # 3. 询问是否查看图片
    print("\n3. 查看选项:")
    print("  1 - 在默认查看器中打开第一个截图")
    print("  2 - 运行图片查看脚本")
    print("  3 - 退出")
    
    try:
        choice = input("请选择 (1-3): ").strip()
        
        if choice == '1':
            # 打开第一个图片
            first_image = image_files[0]
            print(f"正在打开: {first_image}")
            if os.name == 'nt':  # Windows
                os.startfile(first_image)
            elif os.name == 'posix':  # macOS/Linux
                os.system(f'open "{first_image}"' if os.uname().sysname == 'Darwin' 
                         else f'xdg-open "{first_image}"')
        
        elif choice == '2':
            # 运行图片查看脚本
            print("启动图片查看脚本...")
            subprocess.run([sys.executable, 'view_images.py'], cwd='.')
        
        elif choice == '3':
            print("测试完成，再见！")
        
        else:
            print("无效选择")
    
    except KeyboardInterrupt:
        print("\n操作取消")
    except Exception as e:
        print(f"操作时出错: {e}")
    
    print("\n=== 测试结束 ===")
    print("提示:")
    print("- 生成的截图文件保存在当前目录")
    print("- 可以随时运行 'python view_images.py' 来查看图片")
    print("- 可以运行 'python test_screen.py' 进行完整测试")

if __name__ == "__main__":
    main()
