#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的导包示例
展示如何正确导入和使用 PowerShellLanguage
"""
import sys
import os

# 添加项目根目录到Python路径（推荐方法）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 现在可以正常导入
try:
    from core.computer.code.languages.powershell import PowerShellLanguage
    print("✅ 成功导入 PowerShellLanguage")
    
    # 创建实例
    ps = PowerShellLanguage()
    
    # 检查可用性
    if ps.is_available():
        print("✅ PowerShell 可用")
        
        # 简单测试
        test_code = '''
        Write-Host "Hello from PowerShell!"
        Get-Date
        '''
        
        print("执行测试代码...")
        message_queue = ps.run(test_code)
        
        # 读取输出
        while ps.is_running or not message_queue.empty():
            try:
                if not message_queue.empty():
                    message = message_queue.get_nowait()
                    print(f"输出: {message['content'].rstrip()}")
                else:
                    import time
                    time.sleep(0.1)
            except:
                break
        
        print("✅ 测试完成")
        
    else:
        print("❌ PowerShell 不可用")
        
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请检查文件路径和Python路径设置")

# 或者使用更直接的方法
print("\n" + "="*50)
print("方法2: 直接导入（如果脚本在项目根目录）")
print("="*50)

try:
    # 如果您在项目根目录运行，可以直接使用
    from core.computer.code.languages.powershell import PowerShellLanguage
    print("✅ 直接导入成功")
except ImportError as e:
    print(f"❌ 直接导入失败: {e}")
    print("建议使用上面的项目路径方法")
