import time

class BaseLanguage:
    def __init__(self):
        self.is_running = False
        self.start_time = None
        self.elapsed_time = 0
        self.should_stop = False
    
    def run(self, code: str):
        raise NotImplementedError("[BaseLanguage]Subclasses must implement this method")
    
    def get_elapsed_time(self):
        if self.is_running and self.start_time:
            return time.time() - self.start_time
        return self.elapsed_time
    
    def interrupt(self):
        self.should_stop = True