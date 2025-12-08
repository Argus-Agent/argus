"""
基础工具类定义
所有工具都应继承此类以支持OpenAI Function Calling格式
"""

from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
import inspect
import json


class BaseTool(ABC):
    """
    所有工具的基类，定义工具接口和自动schema生成能力
    """
    
    def __init__(self):
        self.name = self.get_name()
        self.description = self.get_description()
        self.parameters_schema = self.get_parameters_schema()
    
    @abstractmethod
    def get_name(self) -> str:
        """返回工具名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """返回工具描述"""
        pass
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        返回参数schema (JSON Schema格式)
        
        Example:
        {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate"},
                "y": {"type": "integer", "description": "Y coordinate"}
            },
            "required": ["x", "y"]
        }
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            执行结果字典，应包含success和其他相关信息
        """
        pass
    
    def to_function_schema(self) -> Dict[str, Any]:
        """
        生成OpenAI Function Calling格式的schema
        
        Returns:
            OpenAI function schema
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证参数是否符合schema
        
        Args:
            params: 要验证的参数
            
        Returns:
            (是否有效, 错误消息或None)
        """
        required = self.parameters_schema.get("required", [])
        properties = self.parameters_schema.get("properties", {})
        
        # 检查必需参数
        for req_param in required:
            if req_param not in params:
                return False, f"缺少必需参数: {req_param}"
        
        # 检查参数类型（简单验证）
        for param_name, param_value in params.items():
            if param_name not in properties:
                return False, f"未知参数: {param_name}"
        
        return True, None


class FunctionTool(BaseTool):
    """
    从普通函数创建工具的便捷类
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters_schema: Dict[str, Any],
        execute_func: Callable
    ):
        self._name = name
        self._description = description
        self._parameters_schema = parameters_schema
        self._execute_func = execute_func
        super().__init__()
    
    def get_name(self) -> str:
        return self._name
    
    def get_description(self) -> str:
        return self._description
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return self._parameters_schema
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            result = self._execute_func(**kwargs)
            if isinstance(result, dict):
                return result
            else:
                return {"success": True, "result": result}
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
