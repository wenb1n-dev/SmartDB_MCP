"""MongoDB execution plan handler.

Runs ``explain`` on a query to produce the execution plan, including
query planner, execution stats, and server info.
"""

import json
from typing import Any, Dict, List, Optional

from bson import json_util

from connection.pool_manager import MultiDBPoolManager
from config.dbconfig import get_db_config_by_name


class MongoDBExplain:
    """Run MongoDB explain on queries."""

    def explain(
        self,
        pool_name: str,
        collection: str,
        operation: str = "find",
        filter_doc: Optional[Dict[str, Any]] = None,
        pipeline: Optional[List[Dict[str, Any]]] = None,
        verbosity: str = "allPlansExecution",
    ) -> str:
        """Run explain on a MongoDB query.

        Args:
            pool_name: Connection pool name.
            collection: Collection name.
            operation: Query operation - "find" or "aggregate".
            filter_doc: Filter document for find operations.
            pipeline: Aggregation pipeline for aggregate operations.
            verbosity: Explain verbosity - "queryPlanner", "executionStats",
                       or "allPlansExecution" (default).

        Returns:
            JSON-formatted execution plan string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        config = get_db_config_by_name(pool_name)
        db_name = config.get("database", "admin")

        with pool.connection() as client:
            db = client[db_name]
            coll = db[collection]

            try:
                # Build the explain command
                if operation.lower() == "find":
                    cmd = {
                        "find": collection,
                        "filter": filter_doc or {},
                    }
                elif operation.lower() == "aggregate":
                    cmd = {
                        "aggregate": collection,
                        "pipeline": pipeline or [],
                        "cursor": {},
                    }
                else:
                    return f"错误: 不支持的操作 '{operation}'，支持: find, aggregate"

                # Run explain
                explain_cmd = {
                    "explain": cmd,
                    "verbosity": verbosity,
                }
                result = db.command(explain_cmd)

                # Format the output
                return self._format_explain(result, operation, collection)

            except Exception as e:
                return f"执行计划分析失败: {str(e)}"

    def _format_explain(self, result: dict, operation: str, collection: str) -> str:
        """Format the explain output for readability."""
        lines = [
            f"=== 执行计划: {operation} '{collection}' ===",
        ]

        # Query planner info
        query_planner = result.get("queryPlanner", {})
        winning_plan = query_planner.get("winningPlan", {})
        rejected_plans = query_planner.get("rejectedPlans", [])

        lines.append("\n--- Query Planner ---")
        lines.append(f"namespace: {query_planner.get('namespace', 'N/A')}")
        lines.append(f"indexFilterSet: {query_planner.get('indexFilterSet', False)}")
        lines.append(f"winning plan stage: {winning_plan.get('stage', 'N/A')}")

        # Recursively describe the plan tree
        self._describe_plan(winning_plan, lines, indent="  ")

        if rejected_plans:
            lines.append(f"\nrejected plans: {len(rejected_plans)}")

        # Execution stats (if available)
        exec_stats = result.get("executionStats")
        if exec_stats:
            lines.append("\n--- Execution Stats ---")
            lines.append(f"executionSuccess: {exec_stats.get('executionSuccess', 'N/A')}")
            lines.append(f"nReturned: {exec_stats.get('nReturned', 'N/A')}")
            lines.append(f"executionTimeMillis: {exec_stats.get('executionTimeMillis', 'N/A')}ms")
            lines.append(f"totalKeysExamined: {exec_stats.get('totalKeysExamined', 'N/A')}")
            lines.append(f"totalDocsExamined: {exec_stats.get('totalDocsExamined', 'N/A')}")

            # Efficiency indicators
            n_returned = exec_stats.get("nReturned", 0)
            docs_examined = exec_stats.get("totalDocsExamined", 0)
            if n_returned and docs_examined and docs_examined > 0:
                efficiency = round(n_returned / docs_examined * 100, 1)
                lines.append(f"scanEfficiency: {efficiency}% (returned/examined)")
                if efficiency < 10:
                    lines.append("⚠️ 警告: 扫描效率低，建议添加合适的索引")

        # Server info
        server_info = result.get("serverInfo", {})
        if server_info:
            lines.append("\n--- Server Info ---")
            lines.append(f"host: {server_info.get('host', 'N/A')}")
            lines.append(f"version: {server_info.get('version', 'N/A')}")

        # Full JSON output
        lines.append("\n--- Full Plan (JSON) ---")
        lines.append(json.dumps(result, default=json_util.default, ensure_ascii=False, indent=2))

        return "\n".join(lines)

    def _describe_plan(self, plan: dict, lines: list, indent: str = ""):
        """Recursively describe the plan tree."""
        if not isinstance(plan, dict):
            return

        stage = plan.get("stage", "N/A")
        lines.append(f"{indent}stage: {stage}")

        if "indexName" in plan:
            lines.append(f"{indent}indexName: {plan['indexName']}")
        if "direction" in plan:
            lines.append(f"{indent}direction: {plan['direction']}")
        if "indexBounds" in plan:
            lines.append(f"{indent}indexBounds: {plan['indexBounds']}")
        if "filter" in plan:
            lines.append(f"{indent}filter: {plan['filter']}")
        if "nReturned" in plan:
            lines.append(f"{indent}nReturned: {plan['nReturned']}")

        # Recurse into input stages
        if "inputStage" in plan:
            self._describe_plan(plan["inputStage"], lines, indent + "  ")
        if "inputStages" in plan:
            for i, sub_stage in enumerate(plan["inputStages"]):
                lines.append(f"{indent}inputStage[{i}]:")
                self._describe_plan(sub_stage, lines, indent + "  ")
