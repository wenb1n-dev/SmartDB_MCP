"""
SQL执行工具类，使用数据库连接池执行SQL语句
"""

import logging
import re
from typing import List, Tuple, Optional, Dict, Any, Set
from dataclasses import dataclass

import sqlparse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DBAPIError

from connection.pool_manager import MultiDBPoolManager
from core.exceptions import SQLPermissionError
from permission import SqlPermissionPolicy, SQLOperation

logger = logging.getLogger(__name__)


@dataclass
class SQLResult:
    """SQL执行结果"""
    success: bool
    message: str
    columns: Optional[List[str]] = None
    rows: Optional[List[Tuple]] = None
    affected_rows: int = 0


class ExecuteSqlUtil:
    """使用数据库连接池的SQL执行工具类"""

    # SQL操作正则模式
    SQL_COMMENT_PATTERN = re.compile(r'--.*$|/\*.*?\*/', re.MULTILINE | re.DOTALL)

    @classmethod
    def execute_single_statement(
        cls,
        pool_name: str,
        statement: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> SQLResult:
        """执行单条SQL语句

        Args:
            pool_name: 线程池名称
            statement: SQL语句
            params: SQL参数字典，用于参数绑定（防止SQL注入）

        Returns:
            SQL执行结果

        Raises:
            Exception: 当执行出错时
        """
        try:

            # 检查权限（使用 pool_name 对应的配置，而非 default 配置）
            operations = ExecuteSqlUtil.extract_operations(statement)

            ExecuteSqlUtil.check_permissions(operations, pool_name)

            pool = MultiDBPoolManager.get_pool(pool_name)
            if pool is None:
                return SQLResult(
                    success=False,
                    message=f"连接池 '{pool_name}' 不存在"
                )

            with pool.connection() as conn:

                # 清理SQL语句并转为大写进行分析
                cleaned_statement = ExecuteSqlUtil.clean_sql(statement)
                upper_statement = cleaned_statement.upper().strip()

                # 判断语句类型
                is_select = (upper_statement.startswith('SELECT') or
                           upper_statement.startswith('WITH'))

                is_show = upper_statement.startswith('SHOW')
                is_explain = upper_statement.startswith('EXPLAIN') and not upper_statement.startswith('EXPLAIN PLAN FOR ')
                is_describe = (upper_statement.startswith('DESCRIBE') or
                             upper_statement.startswith('DESC '))

                # 特殊语句类型（通常返回结果集）
                is_query_type = is_select or is_show or is_explain or is_describe

                try:
                    # 执行SQL语句（支持参数绑定）
                    if params:
                        result = conn.execute(text(statement), params)
                    else:
                        result = conn.execute(text(statement))

                    # 根据语句类型处理结果
                    if is_query_type:
                        # 查询类语句（SELECT, SHOW, EXPLAIN, DESCRIBE等）
                        columns = list(result.keys())
                        rows = result.fetchall()
                        return SQLResult(
                            success=True,
                            message="查询执行成功",
                            columns=columns,
                            rows=rows
                        )
                    else:
                        # 非查询语句（INSERT, UPDATE, DELETE等）
                        conn.commit()
                        return SQLResult(
                            success=True,
                            message="执行成功",
                            affected_rows=result.rowcount
                        )
                except Exception as e:
                    # 如果是非查询语句且执行失败，回滚事务
                    if not is_query_type:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                    raise

        except SQLPermissionError as e:
            logger.warning(f"权限拒绝: {e}, SQL: {statement}")
            return SQLResult(
                success=False,
                message=f"权限不足: {str(e)}"
            )
        except (OperationalError, DBAPIError) as e:
            logger.error(f"数据库连接/操作错误: {e}, SQL: {statement}")
            return SQLResult(
                success=False,
                message=f"数据库操作失败: {str(e)}"
            )
        except SQLAlchemyError as e:
            logger.error(f"SQL执行错误: {e}, SQL: {statement}")
            return SQLResult(
                success=False,
                message=f"SQL执行失败: {str(e)}"
            )
        except Exception as e:
            logger.error(f"未知错误: {e}, SQL: {statement}")
            return SQLResult(
                success=False,
                message=f"执行失败: {str(e)}"
            )

    @classmethod
    def execute_multiple_statements(cls, pool_name: str, query: str) -> List[SQLResult]:
        """执行多条SQL语句

        使用 sqlparse 进行语句分割，正确处理字符串字面量内的分号。

        Args:
            pool_name:  线程池名称
            query: 包含多条SQL语句的查询字符串，以分号分隔

        Returns:
            SQL执行结果列表
        """
        # 使用 sqlparse 分割，正确处理字符串内的分号和注释
        statements = [stmt.strip() for stmt in sqlparse.split(query) if stmt.strip()]
        results = []

        for statement in statements:
            try:
                result = ExecuteSqlUtil.execute_single_statement(pool_name, statement)
                results.append(result)
            except Exception as e:
                logger.warning(f"SQL执行警告: {e}, SQL: {statement}")
                results.append(SQLResult(
                    success=False,
                    message=f"执行失败: {str(e)}"
                ))

        return results

    @classmethod
    def format_result(cls, result: SQLResult) -> str:
        """格式化SQL执行结果

        Args:
            result: SQL执行结果

        Returns:
            格式化后的结果字符串f
        """
        if not result.success:
            return result.message

        if result.columns and result.rows:  # SELECT 类查询结果
            # 将所有值转换为字符串，None转换为"NULL"
            formatted_rows = [
                ",".join("NULL" if v is None else str(v) for v in row)
                for row in result.rows
            ]
            return "\n".join([",".join(result.columns)] + formatted_rows)
        else:  # 非查询语句结果
            return f"{result.message}。影响行数: {result.affected_rows}"

    @staticmethod
    def clean_sql(sql: str) -> str:
        """清理SQL语句，移除注释和多余空白

        Args:
            sql: 原始SQL语句

        Returns:
            清理后的SQL语句
        """
        # 移除注释
        sql = ExecuteSqlUtil.SQL_COMMENT_PATTERN.sub('', sql)
        # 规范化空白字符
        return ' '.join(sql.split())

    @staticmethod
    def extract_operations(sql: str) -> Set[SQLOperation]:
        """提取SQL语句的操作类型

        使用 sqlparse 解析 SQL，仅提取每个语句的首关键字作为操作类型，
        避免误匹配字符串字面量或列名中的关键字（如 ``SELECT * FROM t WHERE c = 'DELETE'``）。

        Args:
            sql: SQL语句

        Returns:
            操作类型集合
        """
        operations: Set[SQLOperation] = set()
        parsed_statements = sqlparse.parse(sql)

        for parsed in parsed_statements:
            # 获取语句的首个 DML/DDL 关键字
            statement_type = parsed.get_type()
            if not statement_type or statement_type == "UNKNOWN":
                # 对于 SHOW/DESCRIBE/EXPLAIN 等 sqlparse 无法识别的语句，
                # 回退到提取首个非空白、非注释 token
                tokens = [
                    t for t in parsed.flatten()
                    if not t.is_whitespace
                    and t.ttype not in sqlparse.tokens.Comment
                ]
                if tokens:
                    first_keyword = tokens[0].value.upper().strip()
                    try:
                        operations.add(SQLOperation.from_str(first_keyword))
                    except ValueError:
                        # 无法识别的关键字，跳过
                        continue
            else:
                # sqlparse 返回的类型是字符串，如 "SELECT"、"INSERT"、"UPDATE"、"DELETE"、
                # "CREATE"、"ALTER"、"DROP" 等
                try:
                    operations.add(SQLOperation.from_str(statement_type))
                except ValueError:
                    continue

        return operations

    @staticmethod
    def check_permissions(operations: Set[SQLOperation], pool_name: str = "default") -> bool:
        """检查操作权限（委托给 SqlPermissionPolicy）

        Args:
            operations: 操作类型集合
            pool_name: 连接池名称，用于获取对应数据库的角色配置

        Returns:
            是否有权限执行所有操作

        Raises:
            SQLPermissionError: 当权限不足时
        """
        policy = SqlPermissionPolicy()
        return policy.check_permissions(pool_name, operations)

