import queue
import shutil
import subprocess
import threading
import time

from ..base_language import BaseLanguage


class PowerShellLanguage(BaseLanguage):
    def __init__(self):
        super().__init__()
        self.process = None

    def is_available(self):
        return shutil.which("powershell") is not None or shutil.which("pwsh") is not None

    def run(self, code: str):
        message = queue.Queue()
        execution_thread = threading.Thread(target=self._execute, args=(code, message))
        execution_thread.daemon = True
        execution_thread.start()
        return message

    def _execute(self, code: str, message: queue.Queue):
        self.is_running = True
        self.start_time = time.time()
        self.should_stop = False
        
        executable = "pwsh" if shutil.which("pwsh") else "powershell"
        
        try:
            # -Command - tells powershell to read command from stdin
            self.process = subprocess.Popen(
                [executable, "-NoProfile", "-Command", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            for line in self.process.stdout:
                if self.should_stop:
                    break
                message.put({"type": "text", "content": line})
            
            return_code = self.process.wait()
            message.put({"type": "text", "content": f"Return code: {return_code}"})
            
        except Exception as e:
            message.put({"type": "error", "content": f"[PowerShellLanguage]Error: {e}"})
        finally:
            self.is_running = False
            self.process = None
            
    def interrupt(self):
        super().interrupt()
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
