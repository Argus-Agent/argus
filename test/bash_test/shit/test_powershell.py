#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerShellLanguage 测试程序
测试功能：
1. 流式读取
2. 含错误的代码读取
3. 中途停止执行
4. 优雅停止执行超时后强制停止
"""

import sys
import os
import time
import threading
from queue import Queue
import importlib.util

# 直接导入，避免相对导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "powershell", 
    os.path.join(current_dir, "languages", "powershell.py")
)
powershell_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(powershell_module)
PowerShellLanguage = powershell_module.PowerShellLanguage


def test_streaming_output():
    """测试1: 流式读取输出"""
    print("=" * 60)
    print("测试1: 流式读取输出")
    print("=" * 60)
    
    ps = PowerShellLanguage()
    
    # 测试代码 - 会产生多行输出
    code = """
Write-Host "开始执行..."
for ($i = 1; $i -le 5; $i++) {
    Write-Host "第 $i 行输出"
    Start-Sleep -Milliseconds 500
}
Write-Host "执行完成!"
"""
    
    print("执行代码:")
    print(code)
    print("-" * 40)
    
    # 开始执行
    message_queue = ps.run(code)
    
    # 流式读取输出
    print("流式输出:")
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                print(f"[{message['type']}] {message['content'].rstrip()}")
            else:
                time.sleep(0.1)
        except:
            break
    
    print(f"执行耗时: {ps.get_elapsed_time():.2f}秒\n")


def test_error_handling():
    """测试2: 含错误的代码读取"""
    print("=" * 60)
    print("测试2: 含错误的代码读取")
    print("=" * 60)
    
    ps = PowerShellLanguage()
    
    # 包含错误的代码
    code = """
Write-Host "正确的代码"
$variable = "测试"
Write-Host $variable

# 故意的错误
Get-NonExistentCommand

Write-Host "这行应该不会执行"
"""
    
    print("执行包含错误的代码:")
    print(code)
    print("-" * 40)
    
    message_queue = ps.run(code)
    
    print("输出（包括错误信息）:")
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                print(f"[{message['type']}] {message['content'].rstrip()}")
            else:
                time.sleep(0.1)
        except:
            break
    
    print(f"执行耗时: {ps.get_elapsed_time():.2f}秒\n")


def test_interrupt_execution():
    """测试3: 中途停止执行"""
    print("=" * 60)
    print("测试3: 中途停止执行")
    print("=" * 60)
    
    ps = PowerShellLanguage()
    
    # 长时间运行的代码
    code = """
Write-Host "开始长时间执行..."
for ($i = 1; $i -le 20; $i++) {
    Write-Host "正在执行第 $i 步..."
    Start-Sleep -Seconds 1
}
Write-Host "正常完成"
"""
    
    print("执行长时间运行的代码:")
    print(code)
    print("-" * 40)
    
    message_queue = ps.run(code)
    
    # 等待3秒后中断
    def interrupt_after_delay():
        time.sleep(3)
        print(">>> 3秒后中断执行...")
        ps.interrupt()
    
    interrupt_thread = threading.Thread(target=interrupt_after_delay)
    interrupt_thread.daemon = True
    interrupt_thread.start()
    
    print("输出（将在3秒后被中断）:")
    start_time = time.time()
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                print(f"[{message['type']}] {message['content'].rstrip()}")
            else:
                time.sleep(0.1)
        except:
            break
    
    print(f"实际执行时间: {time.time() - start_time:.2f}秒\n")


def test_graceful_timeout():
    """测试4: 优雅停止执行超时后强制停止"""
    print("=" * 60)
    print("测试4: 优雅停止执行超时后强制停止")
    print("=" * 60)
    
    ps = PowerShellLanguage()
    
    # 无法正常结束的代码（死循环）
    code = """
Write-Host "开始死循环..."
while ($true) {
    Write-Host "循环中... $(Get-Date)"
    Start-Sleep -Seconds 1
}
"""
    
    print("执行无法正常结束的代码:")
    print(code)
    print("-" * 40)
    
    message_queue = ps.run(code)
    
    # 实现优雅超时停止
    def graceful_timeout():
        print(">>> 尝试优雅停止...")
        ps.interrupt()
        
        # 等待2秒优雅停止
        time.sleep(2)
        
        if ps.is_running:
            print(">>> 优雅停止超时，强制停止...")
            # 这里需要访问内部的 process 来强制停止
            if hasattr(ps, 'process') and ps.process:
                ps.process.kill()
    
    # 3秒后启动超时机制
    timeout_thread = threading.Thread(target=graceful_timeout)
    timeout_thread.daemon = True
    timeout_thread.start()
    
    print("输出（将在3秒后开始优雅停止，2秒后强制停止）:")
    start_time = time.time()
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                print(f"[{message['type']}] {message['content'].rstrip()}")
            else:
                time.sleep(0.1)
        except:
            break
    
    print(f"总执行时间: {time.time() - start_time:.2f}秒\n")


def test_availability():
    """测试PowerShell是否可用"""
    print("=" * 60)
    print("测试PowerShell可用性")
    print("=" * 60)
    
    ps = PowerShellLanguage()
    available = ps.is_available()
    print(f"PowerShell可用: {available}")
    
    if available:
        print("检测到PowerShell环境，可以进行测试")
    else:
        print("未检测到PowerShell环境，跳过测试")
        return False
    
    return True


def main():
    """主测试函数"""
    print("PowerShellLanguage 测试程序")
    print("=" * 60)
    
    # 首先检查PowerShell是否可用
    if not test_availability():
        return
    
    print("\n开始所有测试...")
    
    # 执行所有测试
    test_streaming_output()
    test_error_handling()
    test_interrupt_execution()
    test_graceful_timeout()
    
    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
