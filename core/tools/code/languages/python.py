import logging
import queue
import re
import threading
import time

from jupyter_client.manager import KernelManager

from ..base_language import BaseLanguage


class PythonLanguage(BaseLanguage):
    def __init__(self):
        super().__init__()
        self.km = None
        self.kc = None
        self.current_msg_id = None
    
    def start(self):
        self.should_stop = False
        self.start_time = time.time()
        self.elapsed_time = 0
        
        if self.km:
            self.stop()
        try:
            self.km = KernelManager(kernel_name='python3')
            self.is_running = True
            self.km.start_kernel()
            self.kc = self.km.client()
            self.kc.start_channels()
            self.kc.wait_for_ready()
            logging.info("[PythonLanguage]Started kernel client&manager")
        except Exception as e:
            self.stop()
            logging.error("[PythonLanguage]Error starting kernel: %s", e)

    def stop(self):
        self.is_running = False
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
        self.start_time = None
        
        try:
            if self.km:
                self.km.shutdown_kernel()
                self.is_running = False
                self.km = None
            if self.kc:
                self.kc.stop_channels()
                self.current_msg_id = None
                self.kc = None
            logging.info("[PythonLanguage]Stopped kernel client&manager")
        except Exception as e:
            logging.error("[PythonLanguage]Error during cleanup kernel: %s", e)

    def wait_for_shutdown(self):
        while self.is_running or self.kc:
            time.sleep(0.1)

    def run(self, code: str):
        message = queue.Queue()

        excecution_thread = threading.Thread(target=self._execute_jupyter, args=(code, message))
        excecution_thread.daemon = True
        excecution_thread.start()

        return message

    def _execute_jupyter(self, code: str, message: queue.Queue):
        self.start()

        if self.km.is_alive() is False:
            message.put({"type": "error", "content": "[PythonLanguage]Faild to start Jupyter kernel"})
            return

        # 只在需要时添加matplotlib魔法命令
        if "matplotlib" in code and "%matplotlib" not in code:
            code = "%matplotlib inline\n" + code

        try:
            self.current_msg_id=self.kc.execute(code)
        except Exception as e:
            message.put({"type": "error", "content": f"[PythonLanguage]Error while executing code: {e}"})
            logging.error("[PythonLanguage]Error while executing code: %s", e)
        print("[PythonLanguage]start runing...")
        while True:
            if self.should_stop:
                self.km.interrupt_kernel()

            try:
                msg = self.kc.get_iopub_msg(timeout=1)
            except queue.Empty:
                continue

            if msg['parent_header'].get('msg_id') != self.current_msg_id:
                continue

            msg_type = msg['msg_type']
            content = msg['content']

            print("get_one_msg")

            if msg_type == "stream":
                message.put({"type": "text", "content": content['text']})

            elif msg_type == "error":
                content = "\n".join(content["traceback"])
                # 移除颜色标识
                ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
                content = ansi_escape.sub("", content)
                message.put({"type": "text", "content": content})

            elif msg_type in ["display_data", "execute_result"]:
                data = content["data"]
                if "image/png" in data:
                    message.put({"type": "image/png", "content": data["image/png"]})
                elif "image/jpeg" in data:
                    message.put({"type": "image/jpeg", "content": data["image/jpeg"]})
                elif "text/html" in data:
                    message.put({"type": "html", "content": data["text/html"]})
                elif "text/plain" in data:
                    message.put({"type": "text", "content": data["text/plain"]})
                elif "application/javascript" in data:
                    message.put({"type": "javascript", "content": data["application/javascript"]})

            elif msg_type == 'status':
                if content['execution_state'] == 'idle':
                    break
        print("[PythonLanguage]finished.")
        self.stop()
