import logging
import os
import json
import queue
import threading
from queue import Queue
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

from core.tools import initialize_all_tools, get_global_registry
from core.agents.agent_memory.memory import MemoryManager
from .default_prompt import default_prompt, default_prompt_end


class CodeAgent:
    def __init__(self):
        # Initialize tools registry
        self.tools_registry, self.code_executer = initialize_all_tools()
        
        self.SYSTEM_PROMPT = default_prompt.format(language=str(self.code_executer.language_list))
        logging.info("[CodeAgent]" + self.SYSTEM_PROMPT)
        
        self.SYSTEM_PROMPT_END = default_prompt_end
        self.loop_breakers = ["The task is done.", "The task is impossible.", "任务完成", "任务不可能"]
        
        self.model = os.getenv("CodeAgent_MODEL")
        self.api_base = os.getenv("CodeAgent_API_BASE")
        self.api_key = os.getenv("CodeAgent_API_KEY")
        
        self.stop_agent = False
        
        # Initialize memory manager
        self.memory = MemoryManager(
            agent_name="CodeAgent",
            max_tokens=8000,
            keep_last_screenshots=0,
            keep_function_calls=10,  # 保留更多function call历史
            save_dir="./memory_storage/code_agent",
            model=self.model
        )
        
        # Set system prompt in memory
        self.memory.set_system_prompt(self.SYSTEM_PROMPT)
        
        logging.info(f"[CodeAgent] 已注册工具:\n{self.tools_registry.get_tools_summary()}")

    def _listener(self, message_from_client: Queue):
        """监听来自客户端的信息"""
        while not self.stop_agent:
            try:
                message = message_from_client.get(timeout=0.5)
            except queue.Empty:
                continue
            
            if message["name"] != "CodeAgent":
                message_from_client.put(message)
                continue
            
            if message["type"] == "request":
                if message["content"] == "stop_agent":
                    self.stop_agent = True
                    logging.info("[CodeAgent]用户停止agent")

    def _should_stop(self, ai_content: str = None):
        """检查是否应该停止"""
        if ai_content:
            for loop_breaker in self.loop_breakers:
                if loop_breaker in ai_content:
                    return True
        return False

    def _execute_tool_calls(self, tool_calls, message_to_client):
        """执行工具调用并返回结果"""
        results = self.tools_registry.execute_tool_calls(tool_calls)
        
        for result in results:
            tool_call_id = result.pop("tool_call_id")
            function_name = result.pop("function_name")
            
            # 处理代码执行的特殊输出
            if function_name == "execute_code":
                # 发送代码输出到客户端
                if result.get("outputs"):
                    for output in result["outputs"]:
                        message_to_client.put({
                            "name": "CodeAgent",
                            "type": "text",
                            "content": output
                        })
                
                if result.get("errors"):
                    for error in result["errors"]:
                        message_to_client.put({
                            "name": "CodeAgent",
                            "type": "text",
                            "content": f"[错误] {error}"
                        })
            
            # 记录工具调用结果到memory
            result_text = json.dumps(result, ensure_ascii=False)
            self.memory.add_function_result(tool_call_id, function_name, result_text)
            
            # 发送工具执行状态到客户端
            message_to_client.put({
                "name": "CodeAgent",
                "type": "tool_result",
                "content": {
                    "function": function_name,
                    "success": result.get("success", False)
                }
            })
            
            logging.info(f"[CodeAgent] 工具 {function_name} 执行: {'成功' if result.get('success') else '失败'}")
        
        return results

    def task(self, description: str, message_from_client: Queue, message_to_client: Queue):
        self.stop_agent = False
        
        # Add user task to memory
        self.memory.add("user", description)
        
        listener_thread = threading.Thread(target=self._listener, args=(message_from_client,))
        listener_thread.daemon = True
        listener_thread.start()
        
        logging.info("[CodeAgent][START]")
        message_to_client.put({"name": "CodeAgent", "type": "status", "content": "[START]"})
        
        iteration = 0
        max_iterations = 30
        
        while not self.stop_agent and iteration < max_iterations:
            iteration += 1
            logging.info(f"[CodeAgent] 迭代 {iteration}/{max_iterations}")
            
            # 获取context并调用LLM（带function calling）
            messages = self.memory.get_context()
            tools_schemas = self.tools_registry.get_function_schemas()
            
            try:
                response = completion(
                    model=self.model,
                    api_base=self.api_base,
                    api_key=self.api_key,
                    messages=messages,
                    tools=tools_schemas,
                    tool_choice="auto",
                    stream=False
                )
            except Exception as e:
                logging.error(f"LLM调用失败: {e}")
                message_to_client.put({"name": "CodeAgent", "type": "status", "content": "[ERROR]"})
                message_to_client.put({"name": "CodeAgent", "type": "text", "content": f"错误: {str(e)}"})
                break
            
            message = response.choices[0].message
            
            # 处理文本内容
            if message.content:
                logging.info(f"[CodeAgent] AI回复: {message.content[:100]}...")
                message_to_client.put({
                    "name": "CodeAgent",
                    "type": "ai_content",
                    "content": message.content
                })
                
                # 检查是否想要停止
                if self._should_stop(message.content):
                    logging.info("[CodeAgent] AI表明任务完成")
                    self.memory.add("assistant", message.content)
                    break
            
            # 处理tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls_list = [tc.model_dump() if hasattr(tc, 'model_dump') else tc for tc in message.tool_calls]
                
                # 记录到memory
                self.memory.add_function_call(tool_calls_list, message.content)
                
                # 执行工具
                logging.info(f"[CodeAgent] 执行 {len(tool_calls_list)} 个工具调用")
                message_to_client.put({
                    "name": "CodeAgent",
                    "type": "status",
                    "content": f"[执行工具] {len(tool_calls_list)}个"
                })
                
                results = self._execute_tool_calls(tool_calls_list, message_to_client)
                
                # 添加结束提示
                self.memory.add("user", "工具执行完成。" + self.SYSTEM_PROMPT_END)
                
            else:
                # 没有tool calls，添加assistant回复到memory
                self.memory.add("assistant", message.content or "")
                
                # 如果没有tool calls且没有特殊指示，添加提示
                if not self._should_stop(message.content):
                    self.memory.add("user", "请继续执行任务或使用工具。" + self.SYSTEM_PROMPT_END)
            
            # 检查用户是否停止
            if self.stop_agent:
                logging.info("[CodeAgent][STOP]: 用户停止")
                break
        
        if iteration >= max_iterations:
            logging.warning(f"[CodeAgent] 达到最大迭代次数 {max_iterations}")
            message_to_client.put({"name": "CodeAgent", "type": "text", "content": f"达到最大迭代次数 {max_iterations}"})
        
        logging.info("[CodeAgent][STOP]: 任务完成")
        message_to_client.put({"name": "CodeAgent", "type": "status", "content": "[STOP]"})
        
        return "任务结束"
