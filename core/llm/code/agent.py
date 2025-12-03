import logging
import os
import queue
from queue import Queue

from dotenv import load_dotenv
from litellm import completion

from core.computer.code import Code
from .default_prompt import default_prompt
from .code_parser import CodeParser

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

class CodeAgent:
    def __init__(self):
        self.code_executer = Code()
        self.code_parser = CodeParser
        self.SYSTEM_PROMPT = default_prompt.format(language=str(self.code_executer.language_list))
        self.model = os.getenv("CodeAgent_MODEL")
        self.api_base = os.getenv("CodeAgent_API_BASE")
        self.api_key = os.getenv("CodeAgent_API_KEY")
        self.stop_code = False
        self.stop_agent = False

    def _confirmation(self, message_from_client: Queue, message_to_client: Queue):
        message_to_client.put({"name": "CodeAgent", "type": "request", "content": "code_permission"})
        others = [] # 不是发送给CodeAgent的信息
        result = False
        while True:
            message = message_from_client.get()
            if message["name"] != "CodeAgent":
                others.append(message)
                continue
            if message["type"] == "request":
                if message["content"] == "stop_code":
                    self.stop_code = True
                elif message["content"] == "stop_agent":
                    self.stop_agent = True
                elif message["content"] == "deny":
                    result = False
                    break
                elif message["content"] == "approve":
                    result = True
                    break
        for other in others:
            message_from_client.put(other)
        return result

    def _should_stop(self, message_from_client: Queue):
        try:
            message = message_from_client.get_nowait()
            if message["name"] == "CodeAgent":
                if message["type"] == "request":
                    if message["content"] == "stop_code":
                        self.stop_code = True
                    elif message["content"] == "stop_agent":
                        self.stop_agent = True
            else:
                message_from_client.put(message)  # Put it back if it's not for CodeAgent
        except queue.Empty:
            pass


    def task(self, description: str, message_from_client: Queue, message_to_client: Queue) -> Queue:
        self.stop_code = False
        self.stop_agent = False
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": description}]
        while not self.stop_agent:
            # 检查是否需要停止
            self._should_stop(message_from_client)
            if self.stop_agent:
                message_to_client.put({"name": "CodeAgent", "type": "status", "content": "stop"})
                return

            # 请求ai对话
            response = completion(
                model=self.model,
                api_base=self.api_base,
                api_key=self.api_key,
                messages=messages,
                stream=True,
            )
            # 流式返回
            message_to_client.put({"name": "CodeAgent", "type": "ai_content", "content": "[START]"})
            ai_content = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    message_to_client.put({"name": "CodeAgent", "type": "ai_content", "content": delta})
                    ai_content += delta
            message_to_client.put({"name": "CodeAgent", "type": "ai_content", "content": "[END]"})
            
            # TODO: If the context is too long, use RAG or other methods to handle it
            if len(messages) > 10:
                messages = [messages[0]] + messages[-5:]
            
            messages.append({"role": "assistant", "content": ai_content})

            # 获取模型返回的代码
            codes = CodeParser(ai_content)
            logging.info(f"Find {len(codes)} code blocks. Excuting...")

            # 依次执行代码
            for i in range(len(codes)):
                # 检查是否需要停止
                self._should_stop(message_from_client)
                if self.stop_agent:
                    message_to_client.put({"name": "CodeAgent", "type": "status", "content": "stop"})
                    return
                
                code = codes[i]
                results = self.code_executer.run(*code)
                code_output_content = [{"type": "text", "text": "Code block{i} is executed, and the output is as follows:"}]
                if not self._confirmation(message_from_client, message_to_client):
                    messages.append({"role": "user", "content": f"User rejected to excecute code block{i}"})
                    continue
                while self.code_executer.is_running():

                    # 检查是否需要停止
                    self._should_stop(message_from_client)
                    if self.stop_code or self.stop_agent:
                        break

                    delta = results.get()
                    if delta["type"] == "image/png" or delta["type"] == "image/jpeg":
                        message_to_client.put({"name": "CodeAgent", **delta})
                        code_output_content.append(
                            {
                                "type": "image_url", 
                                "image_url": {"url": delta["content"], "format": delta["type"]}
                            }
                        )
                    else: # 暂时把其他所有内容转为text
                        message_to_client.put({"name": "CodeAgent", "type": "text", "content": delta["content"]})
                        code_output_content.append(
                            {
                                "type": "text",
                                "text": delta["content"]
                            }
                        )
                messages.append({"role": "user", "content": code_output_content})









            
