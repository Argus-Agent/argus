#!/usr/bin/env python3
"""
CodeAgent UI启动脚本
简化版本，用于快速测试UI界面
"""
import os
import sys
import logging
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def main():
    """启动UI的主函数"""
    try:
        # 导入UI模块
        from code_agent_ui import main as ui_main
        
        print("启动 CodeAgent UI...")
        print(f"项目根目录: {project_root}")
        
        # 检查.env文件
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_file):
            print("✓ .env文件存在")
            with open(env_file, 'r', encoding='utf-8') as f:
                print(f"配置内容:\n{f.read()}")
        else:
            print("⚠ .env文件不存在，请确保配置了API信息")
        
        # 启动Flet应用
        ft.app(target=ui_main)
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保安装了所需的库: pip install flet markdown")
    except Exception as e:
        print(f"启动错误: {e}")

if __name__ == "__main__":
    import flet as ft
    logging.basicConfig(
        filename='codeagent_ui_test.log',
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    main()
