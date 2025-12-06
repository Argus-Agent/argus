import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)
from core.llm.code import CodeAgent
import queue
import threading

my_agent = CodeAgent()
message_from_client = queue.Queue()
message_to_client = queue.Queue()

def listener():
    while True:
        msg = message_to_client.get()
        print(f"[{msg['type']}] {msg['content']}")
        if msg["type"] == "status" and msg["content"] == "[STOP]":
            break
        if msg["type"] == "request":
            # 模拟用户批准
            message_from_client.put({"name": "CodeAgent", "type": "request", "content": "approve"})

thread = threading.Thread(target=listener)
thread.daemon = True
thread.start()

result = my_agent.task("生成一个Python函数，计算两个数的和，并打印结果。", message_from_client=message_from_client, message_to_client=message_to_client)

print(f"最终结果: {result}")