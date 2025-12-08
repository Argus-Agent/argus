"""
智能任务路由器 (Smart Task Router)
自动判断任务应该由GUIAgent还是CodeAgent完成
并在失败时自动切换
"""

import logging
import queue
import re
from typing import Tuple, Optional
from litellm import completion
import os
from dotenv import load_dotenv

load_dotenv()

from core.agents.gui_agent.agent import GUIAgent
from core.agents.code_agent.agent import CodeAgent


class SmartRouter:
    """智能路由器 - 自动选择最合适的Agent"""
    
    def __init__(self):
        self.gui_agent = None
        self.code_agent = None
        self.model = os.getenv("GUIAgent_MODEL", "gpt-4o")
        self.api_key = os.getenv("GUIAgent_API_KEY")
        self.api_base = os.getenv("GUIAgent_API_BASE")
        
        # 懒加载agents（只在需要时初始化）
        
    def _get_gui_agent(self):
        """懒加载GUI Agent"""
        if self.gui_agent is None:
            self.gui_agent = GUIAgent()
            logging.info("[SmartRouter] GUIAgent已初始化")
        return self.gui_agent
    
    def _get_code_agent(self):
        """懒加载Code Agent"""
        if self.code_agent is None:
            self.code_agent = CodeAgent()
            logging.info("[SmartRouter] CodeAgent已初始化")
        return self.code_agent
    
    def analyze_task(self, task_description: str) -> Tuple[str, float]:
        """
        分析任务，判断应该使用哪个Agent
        
        Returns:
            (agent_type, confidence): agent类型和置信度
        """
        # 快速规则判断
        gui_keywords = [
            "打开", "点击", "拖拽", "窗口", "界面", "按钮", "菜单", 
            "截图", "屏幕", "鼠标", "键盘输入", "应用", "程序",
            "浏览器", "文件夹", "桌面", "任务栏"
        ]
        
        code_keywords = [
            "计算", "算法", "函数", "变量", "循环", "判断",
            "数据处理", "文件读写", "json", "csv", "api",
            "数学", "统计", "绘图", "分析数据", "print",
            "代码", "脚本", "程序设计"
        ]
        
        task_lower = task_description.lower()
        
        # 计算关键词匹配分数
        gui_score = sum(1 for kw in gui_keywords if kw in task_lower)
        code_score = sum(1 for kw in code_keywords if kw in task_lower)
        
        # 基于规则的快速判断
        if gui_score > code_score:
            return "gui", min(0.6 + gui_score * 0.1, 0.95)
        elif code_score > gui_score:
            return "code", min(0.6 + code_score * 0.1, 0.95)
        
        # 如果不明确，使用LLM分析
        logging.info("[SmartRouter] 规则不明确，使用LLM分析...")
        return self._llm_analyze(task_description)
    
    def _llm_analyze(self, task: str) -> Tuple[str, float]:
        """使用LLM分析任务类型"""
        
        prompt = f"""请分析以下任务应该使用哪种Agent完成：

任务: {task}

可选Agent:
1. GUIAgent - 擅长GUI操作：打开应用、点击按钮、输入文本、窗口管理等
2. CodeAgent - 擅长代码执行：数据计算、文件操作、算法实现、数据分析等

请仅回答：
- 如果应该用GUI: 回答 "GUI:置信度" (如 "GUI:0.9")
- 如果应该用Code: 回答 "CODE:置信度" (如 "CODE:0.85")

回答:"""

        try:
            response = completion(
                model=self.model,
                api_key=self.api_key,
                api_base=self.api_base,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            answer = response.choices[0].message.content.strip().upper()
            
            # 解析回答
            if "GUI" in answer:
                match = re.search(r'GUI:?([\d.]+)', answer)
                confidence = float(match.group(1)) if match else 0.7
                return "gui", confidence
            elif "CODE" in answer:
                match = re.search(r'CODE:?([\d.]+)', answer)
                confidence = float(match.group(1)) if match else 0.7
                return "code", confidence
            else:
                # 默认使用GUI（更安全）
                logging.warning(f"[SmartRouter] LLM回答无法解析: {answer}")
                return "gui", 0.5
                
        except Exception as e:
            logging.error(f"[SmartRouter] LLM分析失败: {e}")
            # 默认GUI
            return "gui", 0.5
    
    def execute_with_fallback(
        self, 
        task: str, 
        msg_from_client: queue.Queue, 
        msg_to_client: queue.Queue,
        force_agent: Optional[str] = None,
        max_retries: int = 2
    ) -> str:
        """
        执行任务，如果失败则自动切换Agent，如果都失败则请求人类介入
        
        Args:
            task: 任务描述
            msg_from_client: 客户端消息队列
            msg_to_client: 服务端消息队列
            force_agent: 强制使用特定agent（"gui"或"code"），None表示自动判断
            max_retries: 最大重试次数（包含人类介入后的重试）
        """
        
        retry_count = 0
        current_task = task
        last_errors = []
        
        while retry_count < max_retries:
            retry_count += 1
            
            # 判断使用哪个Agent
            if force_agent:
                agent_type = force_agent
                confidence = 1.0
                logging.info(f"[SmartRouter] 强制使用 {agent_type.upper()}Agent")
            else:
                agent_type, confidence = self.analyze_task(current_task)
                logging.info(f"[SmartRouter] 任务分析: {agent_type.upper()}Agent (置信度: {confidence:.2f})")
            
            msg_to_client.put({
                "name": "SmartRouter",
                "type": "text",
                "content": f"[路由] 尝试 #{retry_count}: 使用 {agent_type.upper()}Agent (置信度: {confidence:.2f})"
            })
            
            # 第一次尝试
            try:
                if agent_type == "gui":
                    agent = self._get_gui_agent()
                else:
                    agent = self._get_code_agent()
                
                result = agent.task(current_task, msg_from_client, msg_to_client)
                
                # 检查是否成功
                if self._is_success(result):
                    logging.info(f"[SmartRouter] {agent_type.upper()}Agent 成功完成任务")
                    return result
                else:
                    logging.warning(f"[SmartRouter] {agent_type.upper()}Agent 任务失败: {result}")
                    last_errors.append(f"{agent_type}Agent: {result}")
                    raise Exception(f"{agent_type.upper()}Agent执行失败")
                    
            except Exception as e:
                logging.error(f"[SmartRouter] {agent_type.upper()}Agent 失败: {e}")
                last_errors.append(f"{agent_type}Agent: {str(e)}")
                
                # 如果置信度不高且未强制指定，尝试切换
                if confidence < 0.8 and not force_agent:
                    fallback_agent = "code" if agent_type == "gui" else "gui"
                    
                    msg_to_client.put({
                        "name": "SmartRouter",
                        "type": "text",
                        "content": f"[路由] {agent_type.upper()}Agent失败，切换到 {fallback_agent.upper()}Agent"
                    })
                    
                    logging.info(f"[SmartRouter] 切换到 {fallback_agent.upper()}Agent")
                    
                    try:
                        if fallback_agent == "gui":
                            fallback = self._get_gui_agent()
                        else:
                            fallback = self._get_code_agent()
                        
                        result = fallback.task(current_task, msg_from_client, msg_to_client)
                        
                        if self._is_success(result):
                            logging.info(f"[SmartRouter] {fallback_agent.upper()}Agent 成功完成任务")
                            return result
                        else:
                            last_errors.append(f"{fallback_agent}Agent: {result}")
                            logging.error(f"[SmartRouter] {fallback_agent.upper()}Agent 也失败")
                            
                    except Exception as e2:
                        logging.error(f"[SmartRouter] {fallback_agent.upper()}Agent 也失败: {e2}")
                        last_errors.append(f"{fallback_agent}Agent: {str(e2)}")
            
            # 如果到这里说明都失败了，请求人类介入
            if retry_count < max_retries:
                logging.warning("[SmartRouter] 所有Agent都失败，请求人类介入")
                
                msg_to_client.put({
                    "name": "SmartRouter",
                    "type": "human_intervention_needed",
                    "content": {
                        "original_task": task,
                        "current_task": current_task,
                        "errors": last_errors,
                        "retry_count": retry_count,
                        "max_retries": max_retries
                    }
                })
                
                # 等待人类响应
                human_response = self._wait_for_human_intervention(
                    msg_from_client, 
                    msg_to_client,
                    timeout=300  # 5分钟超时
                )
                
                if human_response:
                    action = human_response.get("action")
                    
                    if action == "modify_task":
                        # 人类修改了任务描述
                        current_task = human_response.get("modified_task", task)
                        logging.info(f"[SmartRouter] 人类修改任务为: {current_task}")
                        msg_to_client.put({
                            "name": "SmartRouter",
                            "type": "text",
                            "content": f"[人类介入] 任务已修改，继续执行"
                        })
                        continue
                        
                    elif action == "retry":
                        # 人类要求重试
                        force_agent = human_response.get("force_agent")
                        logging.info(f"[SmartRouter] 人类要求重试")
                        msg_to_client.put({
                            "name": "SmartRouter",
                            "type": "text",
                            "content": f"[人类介入] 重试任务"
                        })
                        continue
                        
                    elif action == "skip":
                        # 人类要求跳过
                        logging.info("[SmartRouter] 人类选择跳过任务")
                        return "任务已跳过（人类介入）"
                    
                    elif action == "completed":
                        # 人类已完成该任务
                        logging.info("[SmartRouter] 人类确认已人工完成任务")
                        return "任务已完成 (人类人工执行)"
                        
                    elif action == "provide_context":
                        # 人类提供额外上下文
                        context = human_response.get("context", "")
                        current_task = f"{current_task}\n\n补充信息: {context}"
                        logging.info(f"[SmartRouter] 人类提供上下文: {context}")
                        msg_to_client.put({
                            "name": "SmartRouter",
                            "type": "text",
                            "content": f"[人类介入] 已添加上下文，继续执行"
                        })
                        continue
                else:
                    # 超时或无响应
                    logging.error("[SmartRouter] 人类介入超时，任务失败")
                    return f"任务失败: 人类介入超时。错误: {'; '.join(last_errors)}"
        
        # 达到最大重试次数
        error_summary = '\n'.join(last_errors)
        return f"任务失败: 已达最大重试次数({max_retries})。\n错误汇总:\n{error_summary}"
    
    def _wait_for_human_intervention(
        self, 
        msg_from_client: queue.Queue,
        msg_to_client: queue.Queue,
        timeout: int = 300
    ) -> Optional[dict]:
        """
        等待人类介入响应
        
        Returns:
            人类的响应字典，包含action和相关参数
        """
        import time
        start_time = time.time()
        
        msg_to_client.put({
            "name": "SmartRouter",
            "type": "text",
            "content": "[等待人类介入] 请提供帮助..."
        })
        
        while time.time() - start_time < timeout:
            try:
                msg = msg_from_client.get(timeout=1)
                
                if msg.get("name") == "SmartRouter" and msg.get("type") == "human_response":
                    logging.info(f"[SmartRouter] 收到人类响应: {msg.get('content')}")
                    return msg.get("content")
                    
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"[SmartRouter] 等待人类介入时出错: {e}")
                
        return None
    
    def _is_success(self, result: str) -> bool:
        """判断任务是否成功"""
        if not isinstance(result, str):
            return False
        
        success_indicators = ["完成", "成功", "finished", "success", "done"]
        failure_indicators = ["失败", "错误", "error", "failed", "超过最大"]
        
        result_lower = result.lower()
        
        # 检查失败标识
        if any(word in result_lower for word in failure_indicators):
            return False
        
        # 检查成功标识
        if any(word in result_lower for word in success_indicators):
            return True
        
        # 默认认为成功（保守策略）
        return True


# 全局实例
_router = None

def get_router() -> SmartRouter:
    """获取全局路由器实例"""
    global _router
    if _router is None:
        _router = SmartRouter()
    return _router
