from typing import Sequence, Any, Dict, Type, ClassVar, List, Optional

from permission.guard import PermissionSpec
from mcp import Tool
from mcp.types import TextContent

from datasource.base import Paradigm


class ToolRegistry:
    """工具注册表，用于管理所有工具实例"""
    _tools: ClassVar[Dict[str, 'ToolsBase']] = {}

    @classmethod
    def register(cls, tool_class: Type['ToolsBase']) -> Type['ToolsBase']:
        """注册工具类

        Args:
            tool_class: 要注册的工具类

        Returns:
            返回注册的工具类，方便作为装饰器使用
        """
        tool = tool_class()
        cls._tools[tool.name] = tool
        return tool_class

    @classmethod
    def get_tool(cls, name: str) -> 'ToolsBase':
        """获取工具实例

        Args:
            name: 工具名称

        Returns:
            工具实例

        Raises:
            ValueError: 当工具不存在时抛出
        """
        if name not in cls._tools:
            raise ValueError(f"未知的工具: {name}")
        return cls._tools[name]

    @classmethod
    def get_all_tools(cls) -> list[Tool]:
        """获取所有工具的描述

        Returns:
            所有工具的描述列表
        """
        return [tool.get_tool_description() for tool in cls._tools.values()]

    @classmethod
    def get_tools_by_paradigms(cls, paradigms: List[Paradigm]) -> list[Tool]:
        """获取适用于指定范式列表的工具描述

        工具的 applicable_paradigms 为空列表时表示适用于所有范式。

        Args:
            paradigms: 当前已注册连接池的范式列表

        Returns:
            适用于指定范式的工具描述列表
        """
        result = []
        for tool in cls._tools.values():
            # Empty applicable_paradigms means universal (all paradigms)
            if not tool.applicable_paradigms:
                result.append(tool.get_tool_description())
            elif any(p in tool.applicable_paradigms for p in paradigms):
                result.append(tool.get_tool_description())
        return result

    @classmethod
    def is_tool_applicable(cls, name: str, paradigm: Paradigm) -> bool:
        """检查工具是否适用于指定范式

        Args:
            name: 工具名称
            paradigm: 要检查的范式

        Returns:
            工具是否适用于该范式
        """
        if name not in cls._tools:
            return False
        tool = cls._tools[name]
        # Empty applicable_paradigms means universal
        if not tool.applicable_paradigms:
            return True
        return paradigm in tool.applicable_paradigms


class ToolsBase:
    """工具基类"""
    name: str = ""
    description: str = ""
    # Applicable paradigms. Empty list means applicable to all paradigms.
    applicable_paradigms: List[Paradigm] = []
    # 工具层权限声明；None 仅允许基类或未注册抽象工具，实际调用必须在映射表中声明
    permission_spec: ClassVar[Optional[PermissionSpec]] = None

    def __init_subclass__(cls, **kwargs):
        """子类初始化时自动注册到工具注册表"""
        super().__init_subclass__(**kwargs)
        if cls.name:  # 只注册有名称的工具
            ToolRegistry.register(cls)

    def get_tool_description(self) -> Tool:
        raise NotImplementedError

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        raise NotImplementedError
