import time
import json
import os
from typing import List, Optional, Dict, Any
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
    消息实体，增加了 'pinned' 属性用于实现选择性记忆保留。
    """
    def __init__(self, role: str, content: str, image_base64: Optional[str] = None, pinned: bool = False):
        self.role = role  # system, user, assistant, tool
        self.content = content
        self.image_base64 = image_base64
        self.pinned = pinned  # 如果为 True，滑动窗口永远不会删除这条消息
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """构造兼容 LLM API 的格式"""
        if not self.image_base64:
            return {"role": self.role, "content": self.content}
        return {
            "role": self.role,
            "content": [
                {"type": "text", "text": self.content},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{self.image_base64}"}}
            ]
        }

    def estimate_tokens(self, model: str = "gpt-4o") -> int:
        """
        估算 Token 数。优先使用 litellm，失败则回退到简易算法。
        """
        # 1. 如果有图片，先计算图片的 Token (保守估计)
        image_tokens = 1100 if self.image_base64 else 0
        
        # 2. 计算文本 Token
        text_tokens = 0
        if litellm:
            try:
                text_tokens = litellm.token_counter(model=model, text=self.content)
            except Exception:
                text_tokens = len(self.content) // 4
        else:
             text_tokens = len(self.content) // 4

        return text_tokens + image_tokens

class MemoryManager:
    """
    混合记忆管理器：
    1. Short-term: 滑动窗口 + 视觉遗忘 + 关键信息Pin住
    2. Long-term:  基于 JSON 的经验/技能库 (Insights)
    """
    def __init__(
        self, 
        agent_name: str = "default_agent",
        max_tokens: int = 8000, 
        keep_last_screenshots: int = 2,
        save_dir: str = "./memory_storage",
        save_dir: str = "./memory_storage",
        model: str = None
    ):
        if model is None:
            model = os.getenv("CodeAgent_MODEL", "gpt-4o")
        self.agent_name = agent_name
        self.history: List[Message] = []
        self.system_prompt: Optional[Message] = None
        self.model = model
        
        # 长期记忆：经验/Insights
        self.insights: Dict[str, str] = {} 
        
        self.max_tokens = max_tokens
        self.keep_last_screenshots = keep_last_screenshots
        
        self.save_dir = save_dir
        self.insights_file = os.path.join(save_dir, f"{agent_name}_insights.json")
        
        self._load_insights()

    def set_system_prompt(self, content: str):
        self.system_prompt = Message("system", content, pinned=True)

    def add(self, role: str, content: str, image_base64: Optional[str] = None, pinned: bool = False):
        """
        添加消息并触发修剪。
        """
        msg = Message(role, content, image_base64, pinned)
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
            if self.insights:
                insights_str = "\n".join([f"- {k}: {v}" for k, v in self.insights.items()])
                final_sys_content += f"\n\n[Recall form Long-term Memory/Experience]:\n{insights_str}"
            
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
                            msg.content = f"[Screenshot Removed] {msg.content}"
                            removed_count += 1
                        else:
                            break

        # --- 2. 基于 Token 的滑动窗口 (Token Pruning) ---
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
            pass # 生产环境中可替换为 logging.error

    def clear_short_term(self):
        """清空对话历史，但保留学到的 Insights"""
        self.history = []