#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerShellLanguage 最终测试程序
测试功能：
1. 流式读取
2. 含错误的代码读取
3. 中途停止执行
4. 优雅停止执行超时后强制停止
这个版本展示了PowerShellLanguage的正确实现和测试方法
"""

import sys
import os
import time
import threading
import subprocess
import queue
import shutil
from queue import Queue

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.computer.code.languages.powershell import PowerShellLanguage
# class BaseLanguage:
#     def __init__(self):
#         self.is_running = False
#         self.start_time = None
#         self.elapsed_time = 0
#         self.should_stop = False
    
#     def run(self, code: str):
#         raise NotImplementedError("[BaseLanguage]Subclasses must implement this method")
    
#     def get_elapsed_time(self):
#         if self.is_running and self.start_time:
#             return time.time() - self.start_time
#         return self.elapsed_time
    
#     def interrupt(self):
#         self.should_stop = True


# class PowerShellLanguage(BaseLanguage):
#     def __init__(self):
#         super().__init__()
#         self.process = None

#     def is_available(self):
#         return shutil.which("powershell") is not None or shutil.which("pwsh") is not None

#     def run(self, code: str):
#         message = queue.Queue()
#         execution_thread = threading.Thread(target=self._execute, args=(code, message))
#         execution_thread.daemon = True
#         execution_thread.start()
#         return message

#     def _execute(self, code: str, message: queue.Queue):
#         self.is_running = True
#         self.start_time = time.time()
#         self.should_stop = False
        
#         executable = "pwsh" if shutil.which("pwsh") else "powershell"
        
#         try:
#             # 修复：使用 -NoProfile 和直接传递代码，而不是通过stdin
#             # 这样可以更好地处理长时间运行的脚本
#             self.process = subprocess.Popen(
#                 [executable, "-NoProfile", "-Command", code],
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.STDOUT,
#                 text=True,
#                 bufsize=1,
#                 universal_newlines=True
#             )
            
#             # 实时读取输出
#             for line in self.process.stdout:
#                 if self.should_stop:
#                     break
#                 message.put({"type": "text", "content": line})
            
#             # 如果被中断，等待进程结束
#             if self.should_stop:
#                 self.process.terminate()
#                 try:
#                     self.process.wait(timeout=3)
#                 except subprocess.TimeoutExpired:
#                     self.process.kill()
#             else:
#                 return_code = self.process.wait()
#                 if return_code != 0:
#                     message.put({"type": "error", "content": f"Process exited with code: {return_code}"})
#                 else:
#                     message.put({"type": "text", "content": f"Return code: {return_code}"})
            
#         except Exception as e:
#             message.put({"type": "error", "content": f"[PowerShellLanguage]Error: {e}"})
#         finally:
#             self.is_running = False
#             self.process = None
            
#     def interrupt(self):
#         self.should_stop = True
#         if self.process:
#             self.process.terminate()
#             try:
#                 self.process.wait(timeout=2)
#             except subprocess.TimeoutExpired:
                # self.process.kill()


def test_streaming_output():
    """测试1: 流式读取输出"""
    print("=" * 60)
    print("测试1: 流式读取输出")
    print("=" * 60)
    
    ps = PowerShellLanguage()
    
    # 测试代码 - 会产生多行输出
    code = '''
Write-Host "=== 开始执行流式测试 ==="
for ($i = 1; $i -le 5; $i++) {
    Write-Host "第 $i 行输出 - $(Get-Date -Format 'HH:mm:ss')"
    Start-Sleep -Milliseconds 800
}
Write-Host "=== 流式测试完成 ==="
'''
    
    print("执行代码:")
    print(code)
    print("-" * 40)
    
    # 开始执行
    message_queue = ps.run(code)
    
    # 流式读取输出
    print("流式输出:")
    output_count = 0
    start_time = time.time()
    
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                output_count += 1
                timestamp = time.strftime('%H:%M:%S')
                print(f"[{timestamp}] [{message['type']}] {message['content'].rstrip()}")
            else:
                time.sleep(0.2)
        except:
            break
    
    total_time = time.time() - start_time
    success = output_count >= 5 and total_time > 3
    print(f"总共收到 {output_count} 条消息")
    print(f"执行耗时: {total_time:.2f}秒")
    print(f"流式测试结果: {'✓ 成功' if success else '✗ 失败'}\n")
    
    return success


def test_error_handling():
    """测试2: 含错误的代码读取"""
    print("=" * 60)
    print("测试2: 含错误的代码读取")
    print("=" * 60)
    
    ps = PowerShellLanguage()
    
    # 包含错误的代码
    code = '''
Write-Host "=== 开始执行错误测试 ==="
$variable = "测试"
Write-Host "正确的变量: $variable"

# 故意的错误
Get-NonExistentCommand

Write-Host "=== 错误测试完成（这行不应该执行）==="
'''
    
    print("执行包含错误的代码:")
    print(code)
    print("-" * 40)
    
    message_queue = ps.run(code)
    
    print("输出（包括错误信息）:")
    error_detected = False
    output_count = 0
    
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                output_count += 1
                print(f"[{message['type']}] {message['content'].rstrip()}")
                
                # 检查是否检测到错误
                if "error" in message['type'].lower() or "Error" in message['content'] or "Get-NonExistentCommand" in message['content']:
                    error_detected = True
                    
            else:
                time.sleep(0.1)
        except:
            break
    
    success = error_detected
    print(f"总共收到 {output_count} 条消息")
    print(f"检测到错误: {error_detected}")
    print(f"错误测试结果: {'✓ 成功' if success else '✗ 失败'}")
    print(f"执行耗时: {ps.get_elapsed_time():.2f}秒\n")
    
    return success


def test_interrupt_execution():
    """测试3: 中途停止执行"""
    print("=" * 60)
    print("测试3: 中途停止执行")
    print("=" * 60)
    
    ps = PowerShellLanguage()
    
    # 长时间运行的代码
    code = '''
Write-Host "=== 开始中断测试 ==="
for ($i = 1; $i -le 30; $i++) {
    Write-Host "执行第 $i 步 - $(Get-Date -Format 'HH:mm:ss')"
    Start-Sleep -Seconds 1
}
Write-Host "=== 中断测试正常完成 ==="
'''
    
    print("执行长时间运行的代码:")
    print(code)
    print("-" * 40)
    
    message_queue = ps.run(code)
    
    # 等待3秒后中断
    def interrupt_after_delay():
        time.sleep(3)
        print(">>> 3秒后执行中断...")
        ps.interrupt()
    
    interrupt_thread = threading.Thread(target=interrupt_after_delay)
    interrupt_thread.daemon = True
    interrupt_thread.start()
    
    print("输出（将在3秒后被中断）:")
    output_count = 0
    start_time = time.time()
    
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                output_count += 1
                timestamp = time.strftime('%H:%M:%S')
                print(f"[{timestamp}] [{message['type']}] {message['content'].rstrip()}")
            else:
                time.sleep(0.2)
        except:
            break
    
    actual_time = time.time() - start_time
    success = actual_time < 5 and actual_time > 2
    print(f"总共收到 {output_count} 条消息")
    print(f"实际执行时间: {actual_time:.2f}秒")
    print(f"中断测试结果: {'✓ 成功' if success else '✗ 失败'}\n")
    
    return success


def test_graceful_timeout():
    """测试4: 优雅停止执行超时后强制停止"""
    print("=" * 60)
    print("测试4: 优雅停止执行超时后强制停止")
    print("=" * 60)
    
    ps = PowerShellLanguage()
    
    # 无法正常结束的代码（死循环）
    code = '''
Write-Host "=== 开始超时测试 ==="
$counter = 0
while ($true) {
    $counter++
    Write-Host "死循环第 $counter 次 - $(Get-Date -Format 'HH:mm:ss')"
    Start-Sleep -Seconds 1
    if ($counter -gt 60) { break }  # 安全上限
}
Write-Host "=== 超时测试完成（不应该到达这里）==="
'''
    
    print("执行无法正常结束的代码:")
    print(code)
    print("-" * 40)
    
    message_queue = ps.run(code)
    
    # 实现优雅超时停止
    def graceful_timeout():
        print(">>> 2秒后尝试优雅停止...")
        time.sleep(2)
        ps.interrupt()
        
        print(">>> 再等待2秒确保停止...")
        time.sleep(2)
        
        if ps.is_running:
            print(">>> 进程仍在运行，但interrupt方法应该已经处理了强制停止")
    
    # 启动超时机制
    timeout_thread = threading.Thread(target=graceful_timeout)
    timeout_thread.daemon = True
    timeout_thread.start()
    
    print("输出（将在2秒后开始优雅停止）:")
    output_count = 0
    start_time = time.time()
    
    while ps.is_running or not message_queue.empty():
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                output_count += 1
                timestamp = time.strftime('%H:%M:%S')
                print(f"[{timestamp}] [{message['type']}] {message['content'].rstrip()}")
            else:
                time.sleep(0.2)
        except:
            break
    
    total_time = time.time() - start_time
    success = total_time < 10
    print(f"总共收到 {output_count} 条消息")
    print(f"总执行时间: {total_time:.2f}秒")
    print(f"超时测试结果: {'✓ 成功' if success else '✗ 失败'}\n")
    
    return success


def test_availability():
    """测试PowerShell是否可用"""
    print("=" * 60)
    print("测试PowerShell可用性")
    print("=" * 60)
    
    ps = PowerShellLanguage()
    available = ps.is_available()
    
    # 检测具体可用的PowerShell版本
    if shutil.which("pwsh"):
        print(f"检测到 PowerShell Core (pwsh): {shutil.which('pwsh')}")
    if shutil.which("powershell"):
        print(f"检测到 Windows PowerShell: {shutil.which('powershell')}")
    
    print(f"PowerShell可用: {available}")
    
    if available:
        print("检测到PowerShell环境，可以进行测试")
    else:
        print("未检测到PowerShell环境，跳过测试")
        return False
    
    return True


def main():
    """主测试函数"""
    print("PowerShellLanguage 最终测试程序")
    print("=" * 60)
    print("测试功能：")
    print("1. 流式读取输出")
    print("2. 含错误的代码读取")
    print("3. 中途停止执行")
    print("4. 优雅停止执行超时后强制停止")
    print("=" * 60)
    
    # 首先检查PowerShell是否可用
    if not test_availability():
        return
    
    print("\n开始所有测试...")
    
    # 执行所有测试并收集结果
    results = {}
    
    results['streaming'] = test_streaming_output()
    results['error'] = test_error_handling()
    results['interrupt'] = test_interrupt_execution()
    results['timeout'] = test_graceful_timeout()
    
    # 输出测试总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    test_names = {
        'streaming': '流式读取输出',
        'error': '含错误的代码读取',
        'interrupt': '中途停止执行',
        'timeout': '优雅停止执行超时后强制停止'
    }
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_names[test_name]}: {status}")
        if result:
            passed += 1
    
    print("-" * 40)
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
