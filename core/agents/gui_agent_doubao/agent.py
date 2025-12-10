import logging
import os
import queue
import threading
import json
from queue import Queue
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

from core.tools import initialize_all_tools, get_global_registry
from core.tools.screen import screen
from core.agents.agent_memory.memory import MemoryManager

from .default_prompt import get_default_prompt


import logging
import os
import queue
import threading
import json
import time
from queue import Queue
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

from core.tools import initialize_all_tools
from core.tools.screen.screen import screen
from core.agents.agent_memory.memory import MemoryManager
from .default_prompt import get_default_prompt
from .action_parser import parse_response, parse_action, map_action_to_function, get_action_coordinates

class GUIAgent:
    def __init__(self):
        self.default_prompt = get_default_prompt(thought=False)
        self.model = os.getenv("GUIAgent_MODEL")
        self.api_base = os.getenv("GUIAgent_API_BASE")
        self.api_key = os.getenv("GUIAgent_API_KEY")
        self.stop_agent = False
        
        # Initialize tools registry (still useful for keeping tools loaded/validated)
        self.tools_registry, _ = initialize_all_tools()
        
        # Initialize memory manager
        self.memory = MemoryManager(
            agent_name="GUIAgent",
            max_tokens=8000,
            keep_last_screenshots=2,
            keep_function_calls=5,
            save_dir="./memory_storage/gui_agent",
            model=self.model
        )
        
        # Set system prompt in memory
        self.memory.set_system_prompt(self.default_prompt)

    def _listener(self, message_from_client: Queue):
        """监听来自客户端的信息"""
        while not self.stop_agent:
            try:
                message = message_from_client.get(timeout=0.5)
            except queue.Empty:
                continue
            
            if message["name"] != "GUIAgent":
                message_from_client.put(message)
                continue
            
            if message["type"] == "request":
                if message["content"] == "stop_agent":
                    self.stop_agent = True
                    logging.info("[GUIAgent]用户停止agent")

    def task(self, description: str, message_from_client: Queue, message_to_client: Queue):
        logging.info("[GUIAgent]任务: %s", description)
        
        # 1. 初始化记忆模块
        # 清空上一轮的短期对话，但保留长期Insights
        self.memory.clear_short_term()
        # 更新 System Prompt 包含当前任务描述
        self.memory.set_system_prompt(self.default_prompt.format(instruction=description))
        
        self.stop_agent = False
        listener_thread = threading.Thread(target=self._listener, args=(message_from_client,))
        listener_thread.daemon = True
        listener_thread.start()
        
        logging.info("[GUIAgent][START]")
        message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[START]"})
        
        iteration = 0
        max_iterations = 50
        
        while not self.stop_agent and iteration < max_iterations:
            iteration += 1
            logging.info(f"[GUIAgent] 迭代 {iteration}/{max_iterations}")
            
            # 2. 截屏
            try:
                screenshot_dict, origin_width, origin_height, offset_left, offset_top = screen.screenshot_base64(
                    resize_factor=0.8
                )
            except Exception as e:
                logging.error(f"截屏失败: {e}")
                return f"任务失败: 截屏错误"
            
            message_to_client.put({"name": "GUIAgent", **screenshot_dict})
            
            # 3. 将截图添加到记忆 (MemoryManager会自动处理图片修剪，只保留最近N张)
            # 注意: 我们添加一个简单的文本content描述，这对VLM有时有帮助
            self.memory.add(
                role="user",
                content="(Current Screen State)", 
                image_base64=screenshot_dict['content']
            )
            
            # 4. 从记忆获取完整上下文
            messages = self.memory.get_context()
            
            # 5. 调用LLM
            try:
                logging.info("[GUIAgent] Waiting for LLM response...")
                response = completion(
                    model=f"volcengine/{self.model}",
                    api_base=self.api_base,
                    api_key=self.api_key,
                    messages=messages,
                    stream=True,
                    # thinking="enabled" # Enable if supported by the model provider
                )
            except Exception as e:
                logging.error(f"LLM调用失败: {e}")
                return f"任务失败: LLM错误"
            
            message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[BEGIN]"})
            
            ai_content = ""
            for chunk in response:
                if self.stop_agent:
                    logging.info("[GUIAgent][STOP]: User stop")
                    message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[STOP]"})
                    return "Task failed: User stopped"
                    
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    message_to_client.put({"name": "GUIAgent", "type": "ai_content", "content": delta})
                    ai_content += delta
            
            message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[END]"})
            
            # 6. 将AI回复添加到记忆
            self.memory.add(role="assistant", content=ai_content)
            
            # 7. 解析并执行动作
            try:
                action_text = parse_response(ai_content)
                action_name, action_args = parse_action(action_text)
                
                logging.info(f"[GUIAgent] Parsed Action: {action_name}, Args: {action_args}")
                
                if action_name == "finished":
                    logging.info(f"[GUIAgent] Finished: {action_args.get('content', '')}")
                    self.stop_agent = True
                    message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[STOP]"})
                    return f"Task finished: {action_args.get('content', '')}"
                
                # 发送可视化坐标点
                action_point = get_action_coordinates(action_name, action_args, origin_width, origin_height)
                if action_point:
                    content = {
                        "x": action_point['x'], 
                        "y": action_point['y'], 
                        "action": action_name
                    }
                    if 'xx' in action_point: content['xx'] = action_point['xx']
                    if 'yy' in action_point: content['yy'] = action_point['yy']
                        
                    message_to_client.put({
                        "name": "GUIAgent", 
                        "type": "action_point", 
                        "content": content
                    })
                
                # 执行函数
                map_action_to_function(
                    action_name, 
                    action_args, 
                    origin_width, 
                    origin_height, 
                    offset_left, 
                    offset_top
                )
                
            except Exception as e:
                logging.error(f"[GUIAgent] Error executing action: {e}", exc_info=True)
                message_to_client.put({"name": "GUIAgent", "type": "status", "content": f"Error: {str(e)}"})
                # 可以选择将错误信息加回记忆，帮助模型下一次纠正
                # self.memory.add(role="system", content=f"Previous action failed: {str(e)}")
        
        message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[STOP]"})
        if iteration >= max_iterations:
            return "Task failed: Max iterations reached"
        return "Task ended"