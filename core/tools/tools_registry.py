"""
工具注册中心
负责管理所有工具、生成function schemas、路由工具调用
"""

from typing import Dict, List, Any, Optional
import json
import logging
from .base_tool import BaseTool


class ToolsRegistry:
    """
    工具注册中心，管理所有可用工具
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.logger = logging.getLogger("ToolsRegistry")
    
    def register(self, tool: BaseTool) -> None:
        """
        注册一个工具
        
        Args:
            tool: 要注册的工具实例
        """
        if tool.name in self.tools:
            self.logger.warning(f"工具 {tool.name} 已存在，将被覆盖")
        
        self.tools[tool.name] = tool
        self.logger.info(f"已注册工具: {tool.name}")
    
    def register_multiple(self, tools: List[BaseTool]) -> None:
        """批量注册工具"""
        for tool in tools:
            self.register(tool)
    
    def unregister(self, tool_name: str) -> bool:
        """
        注销一个工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否成功注销
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.logger.info(f"已注销工具: {tool_name}")
            return True
        return False
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取指定工具"""
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """获取所有工具"""
        return self.tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self.tools.keys())
    
    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的OpenAI function schemas
        
        Returns:
            OpenAI tools格式的schema列表
        """
        return [tool.to_function_schema() for tool in self.tools.values()]
    
    def execute_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            执行结果
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"工具不存在: {tool_name}",
                "available_tools": self.get_tool_names()
            }
        
        # 验证参数
        is_valid, error_msg = tool.validate_parameters(parameters)
        if not is_valid:
            return {
                "success": False,
                "error": f"参数验证失败: {error_msg}",
                "tool_name": tool_name
            }
        
        # 执行工具
        try:
            result = tool.execute(**parameters)
            self.logger.info(f"工具 {tool_name} 执行成功")
            return result
        except Exception as e:
            self.logger.error(f"工具 {tool_name} 执行失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "tool_name": tool_name
            }
    
    def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量执行工具调用（OpenAI格式）
        
        Args:
            tool_calls: OpenAI格式的tool_calls列表
            
        Returns:
            执行结果列表（按顺序）
        """
        results = []
        
        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id")
            function_info = tool_call.get("function", {})
            function_name = function_info.get("name")
            
            # 解析参数
            try:
                if isinstance(function_info.get("arguments"), str):
                    parameters = json.loads(function_info.get("arguments", "{}"))
                else:
                    parameters = function_info.get("arguments", {})
            except json.JSONDecodeError as e:
                results.append({
                    "tool_call_id": tool_call_id,
                    "function_name": function_name,
                    "success": False,
                    "error": f"参数解析失败: {e}"
                })
                continue
            
            # 执行工具
            result = self.execute_tool_call(function_name, parameters)
            results.append({
                "tool_call_id": tool_call_id,
                "function_name": function_name,
                **result
            })
        
        return results
    
    def get_tools_summary(self) -> str:
        """
        获取所有工具的摘要信息（用于日志或调试）
        
        Returns:
            工具摘要字符串
        """
        summary_lines = [f"注册工具总数: {len(self.tools)}"]
        for name, tool in self.tools.items():
            summary_lines.append(f"  - {name}: {tool.description}")
        return "\n".join(summary_lines)


# 全局工具注册中心实例
_global_registry = ToolsRegistry()


def get_global_registry() -> ToolsRegistry:
    """获取全局工具注册中心"""
    return _global_registry
