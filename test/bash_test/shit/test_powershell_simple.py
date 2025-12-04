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
import subprocess
import queue
import shutil
from queue import Queue


class BaseLanguage:
    def __init__(self):
        self.is_running = False
        self.start_time = None
        self.elapsed_time = 0
        self.should_stop = False
    
    def run(self, code: str):
        raise NotImplementedError("[BaseLanguage]Subclasses must implement this method")
    
    def get_elapsed_time(self):
        if self.is_running and self.start_time:
            return time.time() - self.start_time
        return self.elapsed_time
    
    def interrupt(self):
        self.should_stop = True


class PowerShellLanguage(BaseLanguage):
    def __init__(self):
        super().__init__()
        self.process = None

    def is_available(self):
        return shutil.which("powershell") is not None or shutil.which("pwsh") is not None

    def run(self, code: str):
        message = queue.Queue()
        execution_thread = threading.Thread(target=self._execute, args=(code, message))
        execution_thread.daemon = True
        execution_thread.start()
        return message

    def _execute(self, code: str, message: queue.Queue):
        self.is_running = True
        self.start_time = time.time()
        self.should_stop = False
        
        executable = "pwsh" if shutil.which("pwsh") else "powershell"
        
        try:
            # -Command - tells powershell to read command from stdin
            self.process = subprocess.Popen(
                [executable, "-Command", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.process.stdin.write(code)
            self.process.stdin.close()
            
            for line in self.process.stdout:
                message.put({"type": "text", "content": line})
            
            return_code = self.process.wait()
            message.put({"type": "text", "content": f"Return code: {return_code}"})
            
        except Exception as e:
            message.put({"type": "error", "content": f"[PowerShellLanguage]Error: {e}"})
        finally:
            self.is_running = False
            self.process = None
            
    def interrupt(self):
        self.should_stop = True
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()


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
