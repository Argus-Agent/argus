#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerShellLanguage 使用示例
演示如何在实际项目中使用 PowerShellLanguage 类
"""
import time
import threading
import subprocess
import queue
import shutil
import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.computer.code.languages.powershell import PowerShellLanguage

def example_basic_usage():
    """基本使用示例"""
    print("=" * 50)
    print("基本使用示例")
    print("=" * 50)
    
    ps = PowerShellLanguage()
    
    if not ps.is_available():
        print("PowerShell 不可用")
        return
    
    # 简单的 PowerShell 命令
    code = '''
Get-ChildItem | Select-Object Name, Length | Format-Table -AutoSize
'''
    
    print("执行命令:")
    print(code)
    print("-" * 30)
    
    message_queue = ps.run(code)
    
    # 收集所有输出
    output = []
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                if message['type'] == 'text':
                    output.append(message['content'].rstrip())
                    print(message['content'].rstrip())
                else:
                    print(f"错误: {message['content']}")
            else:
                time.sleep(0.1)
        except:
            break
    
    print(f"\n执行完成，耗时: {ps.get_elapsed_time():.2f}秒")


def example_with_timeout():
    """带超时的使用示例"""
    print("=" * 50)
    print("带超时的使用示例")
    print("=" * 50)
    
    ps = PowerShellLanguage()
    
    # 可能长时间运行的命令
    code = '''
Write-Host "开始扫描..."
Get-ChildItem -Path "C:\Windows" -Recurse -ErrorAction SilentlyContinue | 
    Where-Object { $_.Extension -eq ".log" } | 
    Select-Object -First 10 FullName, Length
Write-Host "扫描完成"
'''
    
    print("执行可能耗时的命令（10秒超时）:")
    print(code)
    print("-" * 30)
    
    message_queue = ps.run(code)
    
    # 设置超时机制
    def timeout_handler():
        time.sleep(10)  # 10秒超时
        if ps.is_running:
            print(">>> 命令执行超时，正在中断...")
            ps.interrupt()
    
    timeout_thread = threading.Thread(target=timeout_handler)
    timeout_thread.daemon = True
    timeout_thread.start()
    
    # 收集输出
    output_lines = []
    start_time = time.time()
    
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                if message['type'] == 'text':
                    line = message['content'].rstrip()
                    if line:  # 忽略空行
                        output_lines.append(line)
                        print(line)
                else:
                    print(f"错误: {message['content']}")
            else:
                time.sleep(0.1)
        except:
            break
    
    elapsed = time.time() - start_time
    print(f"\n执行完成，耗时: {elapsed:.2f}秒")
    print(f"输出行数: {len(output_lines)}")


def example_error_handling():
    """错误处理示例"""
    print("=" * 50)
    print("错误处理示例")
    print("=" * 50)
    
    ps = PowerShellLanguage()
    
    # 可能出错的命令
    code = '''
Write-Host "开始执行..."
try {
    # 尝试访问不存在的驱动器
    Get-ChildItem "Z:\nonexistent"
    Write-Host "这不应该显示"
} catch {
    Write-Host "捕获到错误: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host "清理完成"
}
'''
    
    print("执行可能出错的命令:")
    print(code)
    print("-" * 30)
    
    message_queue = ps.run(code)
    
    # 分类收集输出
    normal_output = []
    error_output = []
    
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                content = message['content'].rstrip()
                
                if message['type'] == 'text':
                    normal_output.append(content)
                    print(f"输出: {content}")
                else:
                    error_output.append(content)
                    print(f"错误: {content}")
            else:
                time.sleep(0.1)
        except:
            break
    
    print(f"\n执行统计:")
    print(f"正常输出: {len(normal_output)} 行")
    print(f"错误输出: {len(error_output)} 行")
    print(f"执行耗时: {ps.get_elapsed_time():.2f}秒")


def main():
    """主函数"""
    print("PowerShellLanguage 使用示例")
    print("=" * 50)
    
    # 检查 PowerShell 可用性
    ps = PowerShellLanguage()
    if not ps.is_available():
        print("错误: PowerShell 不可用")
        print("请确保安装了 Windows PowerShell 或 PowerShell Core")
        return
    
    print("PowerShell 可用，开始示例...")
    
    # 运行各种示例
    example_basic_usage()
    print("\n")
    
    example_with_timeout()
    print("\n")
    
    example_error_handling()
    
    print("\n" + "=" * 50)
    print("所有示例运行完成！")


if __name__ == "__main__":
    main()
