from typing import Dict, Any, Sequence

from mcp.types import TextContent


class ToolsBase:

    def execute_sql(self, db_name: str, query: str) -> list:
        raise NotImplementedError