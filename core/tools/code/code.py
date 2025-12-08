"""
代码执行工具 - Function Calling格式
包装原有的代码执行功能为工具
"""

import queue
from .languages import PythonLanguage, BashLanguage, PowerShellLanguage
from ..base_tool import FunctionTool


class Code:
    """代码执行器"""
    
    def __init__(self):
        self.python = PythonLanguage()
        self.bash = BashLanguage()
        self.powershell = PowerShellLanguage()
        self.current_language = None
        self.language_map = {
            "python": self.python,
            "powershell": self.powershell,
            "pwsh": self.powershell,
            "bash": self.bash,
            "sh": self.bash,
        }
        self.language_list = []
        for lang, lang_obj in self.language_map.items():
            if hasattr(lang_obj, 'is_available'):
                if lang_obj.is_available():
                    self.language_list.append(lang)
            else:
                self.language_list.append(lang)

    def run(self, lang: str, code: str):
        """运行代码"""
        lang = lang.lower()
        if lang in self.language_list:
            self.current_language = self.language_map[lang]
            return self.current_language.run(code)
        else:
            message = queue.Queue()
            message.put({"type": "error", "content": f"[Code]不支持的语言:{lang}"})
            return message

    def interrupt(self):
        """中断执行中的代码"""
        message = queue.Queue()
        if self.current_language and self.current_language.is_running:
            self.current_language.interrupt()
            message.put({"type": "text", "content": "代码执行已中断"})
        else:
            message.put({"type": "text", "content": "没有正在运行的代码"})
        return message

    def get_elapsed_time(self):
        """获取代码已运行时间"""
        if self.current_language:
            return self.current_language.get_elapsed_time()

    def is_running(self):
        """代码是否正在运行"""
        return self.current_language and self.current_language.is_running


# ===== Function Calling 工具定义 =====

def create_code_tools():
    """创建所有代码执行工具并返回工具列表"""
    
    # 创建全局Code实例
    code_executor = Code()
    
    tools = []
    
    # Code Execution Tool
    def execute_code_func(language: str, code: str):
        """执行代码工具函数"""
        try:
            result_queue = code_executor.run(language, code)
            
            # 收集所有输出
            outputs = []
            errors = []
            
            while True:
                try:
                    msg = result_queue.get(timeout=0.1)
                    msg_type = msg.get("type", "")
                    content = msg.get("content", "")
                    
                    if msg_type == "text":
                        outputs.append(content)
                    elif msg_type == "error":
                        errors.append(content)
                    elif msg_type == "end":
                        break
                except queue.Empty:
                    # 检查是否还在运行
                    if not code_executor.is_running():
                        break
            
            return {
                "success": len(errors) == 0,
                "language": language,
                "outputs": outputs,
                "errors": errors,
                "output": "\n".join(outputs) if outputs else "",
                "error": "\n".join(errors) if errors else ""
            }
        except Exception as e:
            return {
                "success": False,
                "language": language,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    code_tool = FunctionTool(
        name="execute_code",
        description=f"执行代码。支持的语言: {', '.join(code_executor.language_list)}。代码将在隔离的环境中执行并返回输出",
        parameters_schema={
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": code_executor.language_list,
                    "description": "代码语言"
                },
                "code": {
                    "type": "string",
                    "description": "要执行的代码"
                }
            },
            "required": ["language", "code"]
        },
        execute_func=execute_code_func
    )
    tools.append(code_tool)
    
    # Code Interrupt Tool
    def interrupt_code_func():
        """中断代码执行工具函数"""
        try:
            result_queue = code_executor.interrupt()
            msg = result_queue.get(timeout=1.0)
            return {
                "success": True,
                "message": msg.get("content", ""),
                "was_running": "中断" in msg.get("content", "")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    interrupt_tool = FunctionTool(
        name="interrupt_code",
        description="中断当前正在执行的代码",
        parameters_schema={
            "type": "object",
            "properties": {},
            "required": []
        },
        execute_func=interrupt_code_func
    )
    tools.append(interrupt_tool)
    
    return tools, code_executor