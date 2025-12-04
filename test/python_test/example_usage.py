#!/usr/bin/env python3
"""
代码执行中断和运行时间统计功能使用示例（异步版本）
"""
import logging
import sys
import os
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.computer.code import Code
import time
import threading

def example_usage():
    """
    演示如何使用中断和运行时间统计功能
    """
    code_executor = Code()
    
    # 示例1: 正常执行代码并统计时间
    # print("=== 示例1: 正常执行代码 ===")
    # result_queue = code_executor.run("cmd", "echo Hello, World! && timeout /t 2 && echo 'Done!'")
    #
    # # 读取结果（异步执行需要等待完成）
    # results = []
    # start_time = time.time()
    # timeout = 10  # 10秒超时
    #
    # while time.time() - start_time < timeout:
    #     try:
    #         result = result_queue.get_nowait()
    #         results.append(result)
    #         print(f"输出: {result['text'] if 'text' in result else result}")
    #     except:
    #         # 队列为空，检查是否还在运行
    #         if not code_executor.is_running():
    #             break
    #         time.sleep(0.1)
    #
    # print(f"执行结果: {results}")
    # # 获取运行时间
    # runtime = code_executor.get_elapsed_time()
    # print(f"总运行时间: {runtime}秒")
    # print(f"是否正在运行: {code_executor.is_running()}")
    
    # 示例2: 中断长时间运行的代码
    print("\n=== 示例2: 中断长时间运行的代码 ===")
    
    """在后台运行长时间代码"""
    result_queue = code_executor.run("python", """
import time
print("开始执行长时间任务...")
for i in range(2):
    time.sleep(1)
    print(f"进度: {i+1}/2")
print("任务完成!")
        """)

    
    # 实时读取输出
    print("开始读取输出...")
    results = []
    interrupt_time = 3  # 3秒后中断
    start_time = time.time()
    
    while code_executor.is_running():
        try:
            result = result_queue.get()
            results.append(result)
            print(f"输出: {result}")
        except:
            pass
        
        # 检查是否到中断时间
        if time.time() - start_time >= interrupt_time:
            print("尝试中断代码执行...")
            interrupt_queue = code_executor.interrupt()
            code_executor.current_language.wait_for_shutdown()
            interrupt_result = interrupt_queue.get()
            print(f"{interrupt_result['content']}")
            print("中断操作完成")
            break
        
        time.sleep(0.1)
    
    # 读取剩余结果
    while not result_queue.empty():
        try:
            result = result_queue.get_nowait()
            results.append(result)
            print(f"剩余输出: {result}")
        except:
            pass
    # time.sleep(4)
    print(f"已获得的结果: {results}")
    # 获取中断时的运行时间
    runtime = code_executor.get_elapsed_time()
    print(f"中断时运行时间: {runtime:.2f}秒")
    print(f"是否正在运行: {code_executor.is_running()}")

def monitoring_example():
    """
    演示如何监控代码执行状态
    """
    print("\n=== 示例3: 实时监控代码执行 ===")
    
    code_executor = Code()
    
    def monitor_execution():
        """监控代码执行的线程"""
        while code_executor.is_running():
            runtime = code_executor.get_elapsed_time()
            print(f"代码正在运行，已执行: {runtime:.2f}秒")
            time.sleep(0.1)
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_execution)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # 执行代码
    result_queue = code_executor.run("python", """
import time
print("开始计算...")
total = 0
for i in range(100000000):
    total += i
    if i % 10000000 == 0:
        print(f"计算进度: {i//10000000}/10")
print(f"计算结果: {total}")
    """)
    
    # 实时读取结果
    results = []
    # while code_executor.is_running():
    #     try:
    #         result = result_queue.get_nowait()
    #         results.append(result)
    #         print(f"计算输出: {result}")
    #     except:
    #         pass
    #     if code_executor.get_elapsed_time() > 5:
    #         break
    #     time.sleep(0.1)
    
    # 读取最终结果
    time.sleep(4)
    while not result_queue.empty():
        try:
            result = result_queue.get_nowait()
            results.append(result)
            print(f"4最终输出: {result}")
        except:
            pass
    # time.sleep(4)
    while not result_queue.empty() or code_executor.is_running():
        try:
            result = result_queue.get_nowait()
            results.append(result)
            print(f"最终输出: {result}")
        except:
            pass
    
    print(f"最终结果: {results}")
    # 获取总执行时间
    runtime = code_executor.get_elapsed_time()
    print(f"总执行时间: {runtime:.2f}秒")
    code_executor.current_language.wait_for_shutdown()

if __name__ == "__main__":
    logging.basicConfig(
        filename='example.log',
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    example_usage()
    time.sleep(4)
    logging.info("next test...")
    monitoring_example()
    logging.shutdown()
