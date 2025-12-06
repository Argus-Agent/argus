import logging
import os
import queue
import threading
from queue import Queue
from litellm import completion

import time
from core.computer.mouse import click, double_click, right_click, move, drag, scroll
from core.computer.screen import Screen
from core.computer.keyboard import type_text, press, hotkey, key_down, key_up

from .default_prompt import get_default_prompt

class GUIAgent:
    def __init__(self):
        self.default_prompt = get_default_prompt(thought=False)
        self.model = os.getenv("GUIAgent_MODEL")
        self.api_base = os.getenv("GUIAgent_API_BASE")
        self.api_key = os.getenv("GUIAgent_API_KEY")
        self.stop_agent = False
        self.Screen = Screen()

    def _listener(self, message_from_client: Queue):
        """
        监听来自客户端的信息
        :param message_from_client:
        :return:
        """
        while not self.stop_agent:
            # print("Listening for client messages...")
            try:
                message = message_from_client.get(timeout=0.5)
            except queue.Empty:
                continue
            print("get client message")
            # 不是发给GUIAgent的信息，放回
            if message["name"] != "GUIAgent":
                message_from_client.put(message)
                continue
            if message["type"] == "request":
                # 停止相关
                if message["content"] == "stop_agent":
                    self.stop_agent = True
                    logging.info("[GUIAgent]User stopped agent")

    def task(self, description: str, message_from_client: Queue, message_to_client: Queue):

        logging.info("[GUIAgent]Prompt: %s", self.default_prompt.format(instruction=description))
        messages = [{"role": "system", "content": self.default_prompt.format(instruction=description)}]
        
        self.stop_agent = False
        listener_thread = threading.Thread(target=self._listener, args=(message_from_client,))
        listener_thread.daemon = True
        listener_thread.start()
        logging.info("[GUIAgent][START]")
        message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[START]"})
        while not self.stop_agent:
            screenshot_png, origin_width, origin_height = self.Screen.screenshot_base64(resize_factor=0.8)
            message_to_client.put({"name": "GUIAgent", **screenshot_png})
            messages.append({
                "role": "user", 
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{screenshot_png['type']};base64,{screenshot_png['content']}"
                        }
                    }
                ]
            })
            response = completion(
                model=self.model,
                api_base=self.api_base,
                api_key=self.api_key,
                messages=messages,
                stream=True,
                thinking="disabled",
            )
            message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[BEGIN]"})
            ai_content = ""
            for chunk in response:                
                if self.stop_agent: # 检查是否需要停止
                    logging.info("[GUIAgent][STOP]: User stop")
                    message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[STOP]"})
                    return "Task failed: User stopped"
                if chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    message_to_client.put({"name": "GUIAgent", "type": "ai_content", "content": delta})
                    ai_content += delta
            message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[END]"})
            messages.append({"role": "assistant", "content": ai_content})
            
            # Parse action and execute
            try:
                from .action_parser import parse_response, parse_action, map_action_to_function, get_action_coordinates
                
                action_text = parse_response(ai_content)
                action_name, action_args = parse_action(action_text)
                
                if action_name == "finished":
                    logging.info(f"[GUIAgent] Finished: {action_args.get('content', '')}")
                    self.stop_agent = True
                    message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[STOP]"})
                    return f"Task finished: {action_args.get('content', '')}"

                # Send action coordinates to client
                action_point = get_action_coordinates(action_name, action_args, origin_width, origin_height)
                if action_point:
                    content = {
                        "x": action_point['x'], 
                        "y": action_point['y'], 
                        "action": action_name
                    }
                    if 'xx' in action_point:
                        content['xx'] = action_point['xx']
                    if 'yy' in action_point:
                        content['yy'] = action_point['yy']
                        
                    message_to_client.put({
                        "name": "GUIAgent", 
                        "type": "action_point", 
                        "content": content
                    })

                map_action_to_function(action_name, action_args, origin_width, origin_height)
                # 检查是否需要停止
                if self.stop_agent:
                    logging.info("[GUIAgent][STOP]: User stop")
                    message_to_client.put({"name": "GUIAgent", "type": "status", "content": "[STOP]"})
                    return "Task failed: User stopped"
                
            except Exception as e:
                logging.error(f"[GUIAgent] Error executing action: {e}")
                import traceback
                traceback.print_exc()