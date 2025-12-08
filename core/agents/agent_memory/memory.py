import time
import json
import os
from typing import List, Optional, Dict, Any, Union
from dotenv import load_dotenv

load_dotenv()

try:
    import litellm
    # 抑制 litellm 的详细日志
    litellm.suppress_instrumentation = True
except ImportError:
    litellm = None

class Message:
    """
    消息实体，支持文本、图片和function calling。
    """
    def __init__(
        self, 
        role: str, 
        content: Optional[str] = None, 
        image_base64: Optional[str] = None, 
        pinned: bool = False,
        function_call: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None
    ):
        self.role = role  # system, user, assistant, tool
        self.content = content
        self.image_base64 = image_base64
        self.pinned = pinned
        self.timestamp = time.time()
        
        # Function calling支持
        self.function_call = function_call  # 旧格式兼容
        self.tool_calls = tool_calls  # 新格式
        self.tool_call_id = tool_call_id  # tool role需要的id

    def to_dict(self) -> Dict[str, Any]:
        """构造兼容 LLM API 的格式"""
        result = {"role": self.role}
        
        # 处理tool role
        if self.role == "tool":
            result["tool_call_id"] = self.tool_call_id
            result["content"] = self.content or ""
            return result
        
        # 处理assistant的tool_calls
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
            if self.content:
                result["content"] = self.content
            return result
        
        # 处理图片消息
        if self.image_base64:
            content_list = []
            if self.content:
                content_list.append({"type": "text", "text": self.content})
            content_list.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{self.image_base64}"}})
            result["content"] = content_list
            return result
        
        # 普通文本消息
        result["content"] = self.content or ""
        return result

    def estimate_tokens(self, model: str = "gpt-4o") -> int:
        """
        估算 Token 数。优先使用 litellm，失败则回退到简易算法。
        """
        # 1. 图片 tokens
        image_tokens = 1100 if self.image_base64 else 0
        
        # 2. 文本 tokens
        text_tokens = 0
        if self.content:
            if litellm:
                try:
                    text_tokens = litellm.token_counter(model=model, text=self.content)
                except Exception:
                    text_tokens = len(self.content) // 4
            else:
                text_tokens = len(self.content) // 4
        
        # 3. Function calling tokens (粗略估计)
        function_tokens = 0
        if self.tool_calls:
            # 每个tool call大约50-100 tokens
            function_tokens = len(self.tool_calls) * 75
        elif self.function_call:
            function_tokens = 75

        return text_tokens + image_tokens + function_tokens

class MemoryManager:
    """
    混合记忆管理器：
    1. Short-term: 滑动窗口 + 视觉遗忘 + 关键信息Pin住 + Function Calling历史
    2. Long-term:  基于 JSON 的经验/技能库 (Insights) + Function Calling统计
    """
    def __init__(
        self, 
        agent_name: str = "default_agent",
        max_tokens: int = 8000, 
        keep_last_screenshots: int = 2,
        keep_function_calls: int = 5,  # 保留最近的function call数量
        save_dir: str = "./memory_storage",
        model: str = None
    ):
        if model is None:
            model = os.getenv("CodeAgent_MODEL", "gpt-4o")
        self.agent_name = agent_name
        self.history: List[Message] = []
        self.system_prompt: Optional[Message] = None
        self.model = model
        
        # 长期记忆：经验/Insights + Function统计
        self.insights: Dict[str, str] = {} 
        self.function_stats: Dict[str, int] = {}  # 记录function调用次数
        
        self.max_tokens = max_tokens
        self.keep_last_screenshots = keep_last_screenshots
        self.keep_function_calls = keep_function_calls
        
        self.save_dir = save_dir
        self.insights_file = os.path.join(save_dir, f"{agent_name}_insights.json")
        self.function_stats_file = os.path.join(save_dir, f"{agent_name}_function_stats.json")
        
        self._load_insights()
        self._load_function_stats()

    def set_system_prompt(self, content: str):
        self.system_prompt = Message("system", content, pinned=True)

    def add(
        self, 
        role: str, 
        content: Optional[str] = None, 
        image_base64: Optional[str] = None, 
        pinned: bool = False
    ):
        """
        添加普通消息并触发修剪。
        """
        msg = Message(role, content, image_base64, pinned)
        self.history.append(msg)
        self._prune_history()

    def add_function_call(
        self, 
        tool_calls: List[Dict[str, Any]], 
        assistant_content: Optional[str] = None
    ):
        """
        添加assistant的function calling请求。
        
        Args:
            tool_calls: OpenAI格式的tool_calls列表
            assistant_content: 可选的思考过程文本
        """
        msg = Message(
            role="assistant",
            content=assistant_content,
            tool_calls=tool_calls
        )
        self.history.append(msg)
        
        # 更新function统计
        for tool_call in tool_calls:
            func_name = tool_call.get("function", {}).get("name", "unknown")
            self.function_stats[func_name] = self.function_stats.get(func_name, 0) + 1
        
        self._save_function_stats()
        self._prune_history()

    def add_function_result(
        self, 
        tool_call_id: str, 
        function_name: str,
        result: str
    ):
        """
        添加function执行结果。
        
        Args:
            tool_call_id: 对应的tool call id
            function_name: 函数名称
            result: 执行结果（字符串形式）
        """
        msg = Message(
            role="tool",
            content=result,
            tool_call_id=tool_call_id
        )
        self.history.append(msg)
        self._prune_history()

    def add_insight(self, topic: str, knowledge: str):
        """
        添加长期记忆（经验/技能）。
        """
        self.insights[topic] = knowledge
        self._save_insights()

    def get_context(self) -> List[Dict[str, Any]]:
        """
        构造最终发送给 LLM 的 Context。
        """
        messages = []
        
        # 1. 动态注入长期记忆到 System Prompt
        if self.system_prompt:
            final_sys_content = self.system_prompt.content
            
            # 注入insights
            if self.insights:
                insights_str = "\n".join([f"- {k}: {v}" for k, v in self.insights.items()])
                final_sys_content += f"\n\n[长期记忆/Insights]:\n{insights_str}"
            
            # 注入function统计 (top 5)
            if self.function_stats:
                sorted_funcs = sorted(self.function_stats.items(), key=lambda x: x[1], reverse=True)[:5]
                stats_str = "\n".join([f"- {name}: {count}次" for name, count in sorted_funcs])
                final_sys_content += f"\n\n[常用工具统计]:\n{stats_str}"
            
            sys_msg_dict = {"role": "system", "content": final_sys_content}
            messages.append(sys_msg_dict)
        
        # 2. 添加短期对话历史
        for msg in self.history:
            messages.append(msg.to_dict())
            
        return messages

    def _prune_history(self):
        """
        维护 Context Window 的核心逻辑
        """
        # --- 1. 视觉遗忘 (Visual Pruning) ---
        if self.keep_last_screenshots > 0:
            img_msgs = [m for m in self.history if m.image_base64]
            if len(img_msgs) > self.keep_last_screenshots:
                num_to_remove = len(img_msgs) - self.keep_last_screenshots
                removed_count = 0
                for msg in self.history:
                    if msg.image_base64:
                        if removed_count < num_to_remove:
                            msg.image_base64 = None
                            msg.content = f"[截图已移除] {msg.content or ''}"
                            removed_count += 1
                        else:
                            break

        # --- 2. Function Call 修剪 (保留最近的N组) ---
        if self.keep_function_calls > 0:
            # 找到所有function call对(assistant->tool)
            func_call_pairs = []
            i = 0
            while i < len(self.history):
                msg = self.history[i]
                if msg.tool_calls:
                    # 找到对应的tool responses
                    pair_indices = [i]
                    for j in range(i + 1, len(self.history)):
                        if self.history[j].role == "tool":
                            pair_indices.append(j)
                        else:
                            break
                    func_call_pairs.append(pair_indices)
                i += 1
            
            # 如果超过限制，标记旧的为可删除
            if len(func_call_pairs) > self.keep_function_calls:
                num_to_remove = len(func_call_pairs) - self.keep_function_calls
                for pair_idx in range(num_to_remove):
                    for msg_idx in func_call_pairs[pair_idx]:
                        self.history[msg_idx].pinned = False  # 确保可以被删除

        # --- 3. 基于 Token 的滑动窗口 (Token Pruning) ---
        current_tokens = sum(m.estimate_tokens(self.model) for m in self.history)
        
        while current_tokens > self.max_tokens and len(self.history) > 1:
            # 寻找可以删除的消息（跳过 Pinned 和最后一条）
            remove_index = -1
            for i in range(len(self.history) - 1): 
                if not self.history[i].pinned:
                    remove_index = i
                    break
            
            if remove_index != -1:
                removed_msg = self.history.pop(remove_index)
                current_tokens -= removed_msg.estimate_tokens(self.model)
            else:
                # 极端情况：只能删最早的非 System
                if len(self.history) > 1:
                    self.history.pop(0)
                    current_tokens = sum(m.estimate_tokens(self.model) for m in self.history)
                else:
                    break

    def _load_insights(self):
        if not os.path.exists(self.save_dir):
            try:
                os.makedirs(self.save_dir)
            except OSError:
                pass
        
        if os.path.exists(self.insights_file):
            try:
                with open(self.insights_file, 'r', encoding='utf-8') as f:
                    self.insights = json.load(f)
            except Exception:
                self.insights = {}

    def _save_insights(self):
        try:
            if not os.path.exists(self.save_dir):
                 os.makedirs(self.save_dir)
            with open(self.insights_file, 'w', encoding='utf-8') as f:
                json.dump(self.insights, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_function_stats(self):
        """加载function调用统计"""
        if os.path.exists(self.function_stats_file):
            try:
                with open(self.function_stats_file, 'r', encoding='utf-8') as f:
                    self.function_stats = json.load(f)
            except Exception:
                self.function_stats = {}
        else:
            self.function_stats = {}

    def _save_function_stats(self):
        """保存function调用统计"""
        try:
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)
            with open(self.function_stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.function_stats, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def clear_short_term(self):
        """清空对话历史，但保留学到的 Insights 和 Function 统计"""
        self.history = []

    def get_function_stats(self) -> Dict[str, int]:
        """获取function调用统计"""
        return self.function_stats.copy()