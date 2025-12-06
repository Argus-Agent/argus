#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerShellLanguage 导包示例
展示如何在不同的场景下正确导入 PowerShellLanguage
"""
import sys
import os

# 方法1: 添加当前目录到Python路径（推荐用于测试）
def method1_add_to_path():
    """方法1: 将当前目录添加到Python路径"""
    print("=" * 50)
    print("方法1: 添加当前目录到Python路径")
    print("=" * 50)
    
    # 获取当前文件所在目录的父目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # 将父目录添加到Python路径
    sys.path.insert(0, parent_dir)
    
    try:
        from core.computer.code.languages.powershell import PowerShellLanguage
        from core.computer.code.base_language import BaseLanguage
        
        print("✅ 导入成功!")
        print(f"PowerShellLanguage: {PowerShellLanguage}")
        print(f"BaseLanguage: {BaseLanguage}")
        
        # 测试基本功能
        ps = PowerShellLanguage()
        print(f"PowerShell可用: {ps.is_available()}")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    
    finally:
        # 清理路径
        if parent_dir in sys.path:
            sys.path.remove(parent_dir)


# 方法2: 相对导入（推荐用于包内使用）
def method2_relative_import():
    """方法2: 使用相对导入（需要在包内）"""
    print("\n" + "=" * 50)
    print("方法2: 相对导入（需要在包内使用）")
    print("=" * 50)
    
    print("""
在 core/computer/code/languages/powershell.py 中使用：
    from ..base_language import BaseLanguage

在 core/computer/code/__init__.py 中使用：
    from .languages.powershell import PowerShellLanguage
    from .base_language import BaseLanguage

在 core/computer/__init__.py 中使用：
    from .code.languages.powershell import PowerShellLanguage
    """)


# 方法3: 使用 importlib（动态导入）
def method3_importlib():
    """方法3: 使用 importlib 动态导入"""
    print("\n" + "=" * 50)
    print("方法3: 使用 importlib 动态导入")
    print("=" * 50)
    
    import importlib.util
    
    try:
        # 动态导入 BaseLanguage
        base_path = os.path.join(os.path.dirname(__file__), 'base_language.py')
        base_spec = importlib.util.spec_from_file_location("base_language", base_path)
        base_module = importlib.util.module_from_spec(base_spec)
        base_spec.loader.exec_module(base_module)
        BaseLanguage = base_module.BaseLanguage
        
        # 动态导入 PowerShellLanguage
        ps_path = os.path.join(os.path.dirname(__file__), 'languages', 'powershell.py')
        ps_spec = importlib.util.spec_from_file_location("powershell", ps_path)
        ps_module = importlib.util.module_from_spec(ps_spec)
        
        # 修复导入问题
        ps_module.BaseLanguage = BaseLanguage
        ps_spec.loader.exec_module(ps_module)
        PowerShellLanguage = ps_module.PowerShellLanguage
        
        print("✅ 动态导入成功!")
        print(f"PowerShellLanguage: {PowerShellLanguage}")
        print(f"BaseLanguage: {BaseLanguage}")
        
        # 测试基本功能
        ps = PowerShellLanguage()
        print(f"PowerShell可用: {ps.is_available()}")
        
    except Exception as e:
        print(f"❌ 动态导入失败: {e}")


# 方法4: 修改 sys.path（项目级别）
def method4_project_path():
    """方法4: 修改项目路径（适用于整个项目）"""
    print("\n" + "=" * 50)
    print("方法4: 修改项目路径")
    print("=" * 50)
    
    # 找到项目根目录（agent4目录）
    current_path = os.path.dirname(os.path.abspath(__file__))
    project_root = current_path
    while project_root != os.path.dirname(project_root):
        parent = os.path.dirname(project_root)
        if os.path.basename(parent) == 'agent4':
            project_root = parent
            break
        project_root = parent
    
    print(f"项目根目录: {project_root}")
    
    # 添加项目根目录到Python路径
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        from core.computer.code.languages.powershell import PowerShellLanguage
        from core.computer.code.base_language import BaseLanguage
        
        print("✅ 项目级导入成功!")
        print(f"PowerShellLanguage: {PowerShellLanguage}")
        print(f"BaseLanguage: {BaseLanguage}")
        
        # 测试基本功能
        ps = PowerShellLanguage()
        print(f"PowerShell可用: {ps.is_available()}")
        
    except ImportError as e:
        print(f"❌ 项目级导入失败: {e}")
        print("可能需要创建 __init__.py 文件")


def create_init_files():
    """创建必要的 __init__.py 文件"""
    print("\n" + "=" * 50)
    print("创建必要的 __init__.py 文件")
    print("=" * 50)
    
    init_files = [
        "d:/agent4/__init__.py",
        "d:/agent4/core/__init__.py", 
        "d:/agent4/core/computer/__init__.py",
        "d:/agent4/core/computer/code/__init__.py",
        "d:/agent4/core/computer/code/languages/__init__.py"
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            try:
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write('"""初始化文件"""\n')
                print(f"✅ 创建: {init_file}")
            except Exception as e:
                print(f"❌ 创建失败 {init_file}: {e}")
        else:
            print(f"✅ 已存在: {init_file}")


def main():
    """主函数"""
    print("PowerShellLanguage 导包解决方案")
    print("=" * 60)
    
    # 创建必要的 __init__.py 文件
    create_init_files()
    
    # 演示不同的导入方法
    method1_add_to_path()
    method2_relative_import()
    method3_importlib()
    method4_project_path()
    
    # 推荐的最佳实践
    print("\n" + "=" * 50)
    print("推荐的最佳实践")
    print("=" * 50)
    print("""
1. 在项目根目录运行脚本，使用方法4（修改项目路径）
2. 在测试脚本中，使用方法3（importlib动态导入）
3. 在包内部，使用方法2（相对导入）
4. 简单测试，使用方法1（添加到路径）

推荐配置：
- 在项目根目录创建 __init__.py 文件
- 使用 from core.computer.code.languages.powershell import PowerShellLanguage
- 或使用我们的测试程序中的方法
    """)


if __name__ == "__main__":
    main()
