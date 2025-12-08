#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent4 Main Entry Point
智能路由模式：自动选择最佳Agent并支持失败切换
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

from core.agents.smart_router import get_router


def run_smart_agent(task_description: str, force_agent: str = None):
    """使用智能路由器运行任务"""
    print(f"\n{'='*60}")
    print(f"🤖 智能任务路由器")
    print(f"任务: {task_description}")
    if force_agent:
        print(f"强制模式: {force_agent.upper()}Agent")
    else:
        print(f"模式: 自动判断 + 失败切换")
    print(f"{'='*60}\n")
    
    router = get_router()
    message_from_client = queue.Queue()
    message_to_client = queue.Queue()
    
    # 启动消息监听线程
    stop_flag = threading.Event()
    
    def listen_to_agent():
        while not stop_flag.is_set():
            try:
                msg = message_to_client.get(timeout=0.5)
                msg_type = msg.get('type', '')
                content = msg.get('content', '')
                
                if msg_type == 'status':
                    if content == '[START]':
                        print("[状态] Agent已启动")
                    elif content == '[STOP]':
                        print("\n[状态] Agent已停止")
                        stop_flag.set()
                        break
                    elif 'BLOCK' in content:
                        print(f"\n[代码块] {content}")
                elif msg_type == 'ai_content':
                    if content not in ['[BEGIN]', '[END]']:
                        print(content, end='', flush=True)
                elif msg_type == 'text':
                    print(f"\n{content}")
                elif msg_type == 'tool_result':
                    tool_info = content
                    print(f"\n[工具] {tool_info.get('function')}: {'成功' if tool_info.get('success') else '失败'}")
                elif msg_type == 'request' and 'need_permission' in content:
                    # 代码执行权限（自动批准）
                    print("\n[请求] 自动批准代码执行")
                    message_from_client.put({"type": "request", "content": "approve"})
                    
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"消息监听错误: {e}")
    
    listener = threading.Thread(target=listen_to_agent, daemon=True)
    listener.start()
    
    # 运行任务
    try:
        result = router.execute_with_fallback(
            task_description, 
            message_from_client, 
            message_to_client,
            force_agent=force_agent
        )
        print(f"\n\n✓ 任务结果: {result}")
    except KeyboardInterrupt:
        print("\n用户中断")
        stop_flag.set()
    except Exception as e:
        logging.error(f"执行错误: {e}", exc_info=True)
        print(f"\n✗ 错误: {e}")
    
    stop_flag.set()
    listener.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(
        description='Agent4 - 智能任务路由器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 自动判断并执行
  python main.py --task "打开记事本"
  python main.py --task "计算1到100的和"
  
  # 强制使用特定Agent
  python main.py --task "打开记事本" --force gui
  python main.py --task "数据分析" --force code
        """
    )
    parser.add_argument('--task', type=str, required=True, help='任务描述')
    parser.add_argument(
        '--force', 
        type=str, 
        choices=['gui', 'code'], 
        help='强制使用特定Agent（gui或code）'
    )
    
    args = parser.parse_args()
    
    # 检查环境变量
    required_env = ['GUIAgent_MODEL', 'GUIAgent_API_KEY', 'GUIAgent_API_BASE']
    missing_env = [env for env in required_env if not os.getenv(env)]
    
    if missing_env:
        print(f"❌ 错误: 缺少环境变量: {', '.join(missing_env)}")
        print("请检查 .env 文件是否正确配置")
        sys.exit(1)
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent4 Main Entry Point
智能路由模式：自动选择最佳Agent并支持失败切换
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

from core.agents.smart_router import get_router


def run_smart_agent(task_description: str, force_agent: str = None):
    """使用智能路由器运行任务"""
    print(f"\n{'='*60}")
    print(f"🤖 智能任务路由器")
    print(f"任务: {task_description}")
    if force_agent:
        print(f"强制模式: {force_agent.upper()}Agent")
    else:
        print(f"模式: 自动判断 + 失败切换")
    print(f"{'='*60}\n")
    
    router = get_router()
    message_from_client = queue.Queue()
    message_to_client = queue.Queue()
    
    # 启动消息监听线程
    stop_flag = threading.Event()
    
    def listen_to_agent():
        while not stop_flag.is_set():
            try:
                msg = message_to_client.get(timeout=0.5)
                msg_type = msg.get('type', '')
                content = msg.get('content', '')
                
                if msg_type == 'status':
                    if content == '[START]':
                        print("[状态] Agent已启动")
                    elif content == '[STOP]':
                        print("\n[状态] Agent已停止")
                        stop_flag.set()
                        break
                    elif 'BLOCK' in content:
                        print(f"\n[代码块] {content}")
                elif msg_type == 'ai_content':
                    if content not in ['[BEGIN]', '[END]']:
                        print(content, end='', flush=True)
                elif msg_type == 'text':
                    print(f"\n{content}")
                elif msg_type == 'tool_result':
                    tool_info = content
                    print(f"\n[工具] {tool_info.get('function')}: {'成功' if tool_info.get('success') else '失败'}")
                elif msg_type == 'request' and 'need_permission' in content:
                    # 代码执行权限（自动批准）
                    print("\n[请求] 自动批准代码执行")
                    message_from_client.put({"type": "request", "content": "approve"})
                    
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"消息监听错误: {e}")
    
    listener = threading.Thread(target=listen_to_agent, daemon=True)
    listener.start()
    
    # 运行任务
    try:
        result = router.execute_with_fallback(
            task_description, 
            message_from_client, 
            message_to_client,
            force_agent=force_agent
        )
        print(f"\n\n✓ 任务结果: {result}")
    except KeyboardInterrupt:
        print("\n用户中断")
        stop_flag.set()
    except Exception as e:
        logging.error(f"执行错误: {e}", exc_info=True)
        print(f"\n✗ 错误: {e}")
    
    stop_flag.set()
    listener.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(
        description='Agent4 - 智能任务路由器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 自动判断并执行
  python main.py --task "打开记事本"
  python main.py --task "计算1到100的和"
  
  # 强制使用特定Agent
  python main.py --task "打开记事本" --force gui
  python main.py --task "数据分析" --force code
        """
    )
    parser.add_argument('--task', type=str, required=True, help='任务描述')
    parser.add_argument(
        '--force', 
        type=str, 
        choices=['gui', 'code'], 
        help='强制使用特定Agent（gui或code）'
    )
    
    args = parser.parse_args()
    
    # 检查环境变量
    required_env = ['GUIAgent_MODEL', 'GUIAgent_API_KEY', 'GUIAgent_API_BASE']
    missing_env = [env for env in required_env if not os.getenv(env)]
    
    if missing_env:
        print(f"❌ 错误: 缺少环境变量: {', '.join(missing_env)}")
        print("请检查 .env 文件是否正确配置")
        sys.exit(1)
    
    # 运行智能路由器
    run_smart_agent(args.task, args.force)


if __name__ == "__main__":
    # 如果没有参数，启动图形界面
    if len(sys.argv) == 1:
        print("启动 Agent4 Liquid Bar UI...")
        try:
            from core.ui.app import LiquidBar
            app = LiquidBar()
            app.protocol("WM_DELETE_WINDOW", app.on_closing)
            app.mainloop()
        except ImportError as e:
            print(f"UI依赖缺失: {e}")
            print("请运行: pip install customtkinter pillow")
        except Exception as e:
            print(f"UI启动失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        # 有参数，进入命令行模式
        main()
