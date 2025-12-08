#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent4 Main Entry Point
支持启动 GUIAgent 和 CodeAgent
"""

import os
import sys
import argparse
import queue
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.llm.gui.agent import GUIAgent
from core.llm.code.agent import CodeAgent

def run_gui_agent(task_description: str):
    """运行 GUI Agent"""
    print(f"\n{'='*60}")
    print(f"启动 GUI Agent")
    print(f"任务: {task_description}")
    print(f"{'='*60}\n")
    
    agent = GUIAgent()
    message_from_client = queue.Queue()
    message_to_client = queue.Queue()
    
    # 启动消息监听线程
    def listen_to_agent():
        while True:
            try:
                msg = message_to_client.get(timeout=1)
                msg_type = msg.get('type', '')
                content = msg.get('content', '')
                
                if msg_type == 'status':
                    print(f"[状态] {content}")
                    if content == '[STOP]':
                        break
                elif msg_type == 'ai_content':
                    if content not in ['[BEGIN]', '[END]']:
                        print(content, end='', flush=True)
                elif msg_type == 'action_point':
                    print(f"\n[动作] {content}")
                    
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"消息监听错误: {e}")
                break
    
    listener = threading.Thread(target=listen_to_agent, daemon=True)
    listener.start()
    
    # 运行任务
    try:
        result = agent.task(task_description, message_from_client, message_to_client)
        print(f"\n\n任务完成: {result}")
    except KeyboardInterrupt:
        print("\n用户中断")
        message_from_client.put({"name": "GUIAgent", "type": "request", "content": "stop_agent"})
    except Exception as e:
        logging.error(f"GUI Agent 错误: {e}", exc_info=True)
    
    listener.join(timeout=2)

def run_code_agent(task_description: str):
    """运行 Code Agent"""
    print(f"\n{'='*60}")
    print(f"启动 Code Agent")
    print(f"任务: {task_description}")
    print(f"{'='*60}\n")
    
    agent = CodeAgent()
    message_from_client = queue.Queue()
    message_to_client = queue.Queue()
    
    # 启动消息监听和交互线程
    stop_flag = threading.Event()
    
    def listen_to_agent():
        current_block = None
        while not stop_flag.is_set():
            try:
                msg = message_to_client.get(timeout=0.5)
                msg_type = msg.get('type', '')
                content = msg.get('content', '')
                
                if msg_type == 'status':
                    if 'BLOCK' in content:
                        current_block = content
                        print(f"\n{'='*50}")
                        print(f"[代码块] {content}")
                        print(f"{'='*50}")
                    elif content == '[START]':
                        print("[状态] Agent 已启动")
                    elif content == '[STOP]':
                        print("\n[状态] Agent 已停止")
                        stop_flag.set()
                        break
                        
                elif msg_type == 'request' and 'need_permission' in content:
                    print(f"\n[请求] 是否执行代码块 {current_block}?")
                    print("输入 'y' 同意, 'n' 拒绝, 'stop' 停止agent: ", end='', flush=True)
                    
                    # 自动批准（调试模式）
                    response = 'y'  # 可以改为 input() 以交互模式运行
                    print(response)
                    
                    if response.lower() == 'y':
                        message_from_client.put({"name": "CodeAgent", "type": "request", "content": "approve"})
                    elif response.lower() == 'stop':
                        message_from_client.put({"name": "CodeAgent", "type": "request", "content": "stop_agent"})
                    else:
                        message_from_client.put({"name": "CodeAgent", "type": "request", "content": "deny"})
                        
                elif msg_type == 'ai_content':
                    if content not in ['[BEGIN]', '[END]']:
                        print(content, end='', flush=True)
                        
                elif msg_type == 'text':
                    print(f"[输出] {content}")
                    
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"消息监听错误: {e}")
    
    listener = threading.Thread(target=listen_to_agent, daemon=True)
    listener.start()
    
    # 运行任务
    try:
        result = agent.task(task_description, message_from_client, message_to_client)
        print(f"\n\n任务结果: {result}")
    except KeyboardInterrupt:
        print("\n用户中断")
        message_from_client.put({"name": "CodeAgent", "type": "request", "content": "stop_agent"})
    except Exception as e:
        logging.error(f"Code Agent 错误: {e}", exc_info=True)
    
    stop_flag.set()
    listener.join(timeout=2)

def main():
    parser = argparse.ArgumentParser(description='Agent4 - GUI and Code Agent')
    parser.add_argument('--mode', type=str, choices=['gui', 'code'], required=True,
                        help='选择运行模式: gui 或 code')
    parser.add_argument('--task', type=str, required=True,
                        help='任务描述')
    
    args = parser.parse_args()
    
    # 检查环境变量
    if args.mode == 'gui':
        required_env = ['GUIAgent_MODEL', 'GUIAgent_API_KEY', 'GUIAgent_API_BASE']
    else:
        required_env = ['CodeAgent_MODEL', 'CodeAgent_API_KEY', 'CodeAgent_API_BASE']
    
    missing_env = [env for env in required_env if not os.getenv(env)]
    if missing_env:
        print(f"错误: 缺少环境变量: {', '.join(missing_env)}")
        print("请检查 .env 文件是否正确配置")
        sys.exit(1)
    
    # 运行对应的 Agent
    if args.mode == 'gui':
        run_gui_agent(args.task)
    else:
        run_code_agent(args.task)

if __name__ == "__main__":
    # 如果没有参数，显示使用示例
    if len(sys.argv) == 1:
        print("Agent4 - GUI and Code Agent")
        print("\n使用示例:")
        print('  python main.py --mode code --task "打印Hello World"')
        print('  python main.py --mode gui --task "打开记事本"')
        print("\n更多帮助:")
        print("  python main.py --help")
        sys.exit(0)
    
    main()
