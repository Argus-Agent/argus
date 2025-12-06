import logging
import os
import time
import queue
import threading
from queue import Queue
from litellm import completion
from core.computer.code import Code
from .default_prompt import default_prompt, default_prompt_end
from .code_parser import CodeParser

class CodeAgent:
    def __init__(self):
        self.code_executer = Code()
        self.SYSTEM_PROMPT = default_prompt.format(language=str(self.code_executer.language_list))
        logging.info("[CodeAgent]"+self.SYSTEM_PROMPT)
        self.SYSTEM_PROMPT_END = default_prompt_end
        self.loop_breakers = ["The task is done.", "The task is impossible."]
        self.model = os.getenv("CodeAgent_MODEL")
        self.api_base = os.getenv("CodeAgent_API_BASE")
        self.api_key = os.getenv("CodeAgent_API_KEY")
        self.stop_code = False
        self.stop_agent = False
        self.permission = None

    def _listener(self, message_from_client: Queue):
        """
        监听来自客户端的信息
        :param message_from_client:
        :return:
        """
        while not self.stop_agent:
            try:
                message = message_from_client.get(timeout=0.5)
            except queue.Empty:
                continue
            print("get client message")
            # 不是发给CodeAgent的信息，放回
            if message["name"] != "CodeAgent":
                message_from_client.put(message)
                continue
            if message["type"] == "request":
                # 允许执行代码
                if message["content"] == "deny":
                    self.permission = False
                    logging.info("[CodeAgent]User denied execution")
                elif message["content"] == "approve":
                    self.permission = True
                    logging.info("[CodeAgent]User approved execution")
                # 停止相关
                elif message["content"] == "stop_agent":
                    self.stop_agent = True
                    logging.info("[CodeAgent]User stopped agent")
                elif message["content"] == "stop_code":
                    self.stop_code = True
                    logging.info("[CodeAgent]User stopped code execution")

    def _should_stop(self, ai_content: str = None):
        if ai_content:
            for loop_breaker in self.loop_breakers:
                if loop_breaker in ai_content:
                    return True
        return False

    def task(self, description: str, message_from_client: Queue, message_to_client: Queue):
        self.stop_agent = False
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": description}]
        listener_thread = threading.Thread(target=self._listener, args=(message_from_client,))
        listener_thread.daemon = True
        listener_thread.start()
        logging.info("[CodeAgent][START]")
        message_to_client.put({"name": "CodeAgent", "type": "status", "content": "[START]"})
        
        while not self.stop_agent:
            # 请求ai对话
            response = completion(
                model=self.model,
                api_base=self.api_base,
                api_key=self.api_key,
                messages=messages,
                stream=True,
            )
            # 流式返回
            message_to_client.put({"name": "CodeAgent", "type": "ai_content", "content": "[BEGIN]"})
            ai_content = ""
            for chunk in response:
                # 检查是否需要停止
                if self.stop_agent:
                    logging.info("[CodeAgent][STOP]: User stop")
                    message_to_client.put({"name": "CodeAgent", "type": "status", "content": "[STOP]"})
                    return
                if chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    message_to_client.put({"name": "CodeAgent", "type": "ai_content", "content": delta})
                    ai_content += delta
            message_to_client.put({"name": "CodeAgent", "type": "ai_content", "content": "[END]"})
            messages.append({"role": "assistant", "content": ai_content})
            
            # 检查ai是否想要停止
            if self._should_stop(ai_content):
                break

            # TODO: If the context is too long, use RAG or other methods to handle it
            # if len(messages) > 10:
            #     messages = [messages[0]] + messages[-5:]

            # 获取模型返回的代码
            codes = CodeParser(ai_content)
            if not codes:
                messages.append({"role": "user", "content": "No code blocks found. Skip execution. " + self.SYSTEM_PROMPT_END})
                continue

            # 依次执行代码
            logging.info(f"Find {len(codes)} code blocks. Executing...")
            for i in range(len(codes)):

                logging.info(f"Executing code block {i}..., code: {codes[i]}")
                code = codes[i]
                self.permission = None
                message_to_client.put({"name": "CodeAgent", "type": "status", "content": f"[BLOCK{i}]"})
                message_to_client.put({"name": "CodeAgent", "type": "request", "content": f"[BLOCK{i}]need_permission"})

                # 阻塞等待客户端返回允许结果
                print("wtf???")
                while self.permission is None:
                    logging.info("waiting permission")
                    print("waiting permission")
                    # 检查是否需要停止
                    time.sleep(0.5)
                    if self.stop_agent:
                        logging.info("[CodeAgent][STOP]: User stop")
                        message_to_client.put({"name": "CodeAgent", "type": "status", "content": "[STOP]"})
                        return
                if not self.permission:
                    logging.info(f"User rejected to excecute code block{i}")
                    messages.append({"role": "user", "content": f"User rejected to excecute code block{i}"})
                    continue
                
                logging.info(f"User approved to excecute code block {i}, start executing")
                results = self.code_executer.run(lang=code["lang"], code=code["code"]) # 正确解包
                code_output_content = [{"type": "text", "text": f"Code block{i} is executed, and the output is as follows:"}]
                
                self.stop_code = False
                while self.code_executer.is_running() or not results.empty():
                    logging.info(f"[CodeAgent]: Code block{i} is running, code_executer:{self.code_executer.is_running()}, results.empty():{results.empty()}")
                    # 检查是否需要停止
                    if self.stop_code or self.stop_agent:
                        self.code_executer.interrupt()
                        break

                    try:
                        delta = results.get(timeout=0.2)
                    except queue.Empty:
                        continue

                    # TODO: 有bug，图片先不返回
                    if delta["type"] == "image/png" or delta["type"] == "image/jpeg":
                        # pass
                        message_to_client.put({"name": "CodeAgent", **delta})
                        code_output_content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{delta["type"]};base64,{delta["content"]}"
                                }
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

                logging.info(f"Finish executing code block {i}")
                messages.append({"role": "user", "content": code_output_content})

            messages.append({"role": "user", "content": "All code blocks are executed. " + self.SYSTEM_PROMPT_END})
        
        logging.info("[CodeAgent][STOP]: task finished")
        message_to_client.put({"name": "CodeAgent", "type": "status", "content": "[STOP]"})
        return messages[-1]["content"]

        









            
