import os
import logging
import queue
import threading
from queue import Queue

import code_praser
from dotenv import load_dotenv
from litellm import completion

from default_prompt import default_prompt
from core.computer.code import Code
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

class CodeAgent:
    def __init__(self):
        self.code_exceuter = Code()
        self.SYSTEM_PROMPT = default_prompt.format(language=str(self.code_exceuter.language_list))
        self.model = os.getenv("AgentCode_MODEL")
        self.api_base = os.getenv("AgentCode_API_BASE")
        self.api_key = os.getenv("AgentCode_API_KEY")

    def task(self, description: str, message_in: Queue):
        message_out = queue.Queue()
        excecution_thread = threading.Thread(target=self._task_async, args=(description, message_in, message_out))
        excecution_thread.daemon = True
        excecution_thread.start()
        return message_out
    def _task_async(self, description: str, message_in: Queue, message_out: Queue):
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": description}]
        while True:
            response = completion(
                model=self.model,
                api_base=self.api_base,
                api_key=self.api_key,
                messages=messages
            )
            ai_content = response.choices[0].message.content
            codes = code_praser.CodePraser(ai_content)
            logging.info(f"Find {len(codes)} code blocks. Excuting...")
            for i in range(len(codes)):
                code = codes[i]
                results = self.code_exceuter.run(*code)
                result = ""
                if not conformation():
                    messages.append({"role": "user", "content": f"User rejected to excecute code block{i}"})
                while self.code_exceuter.is_running():
                    result = "\n".join(str(results.get()))
                    if






            
