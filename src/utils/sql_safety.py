"""SQL safety utilities for identifier validation and parameter binding helpers."""

import re
from typing import List, Tuple, Dict, Any

# Valid SQL identifier pattern: starts with letter or underscore, followed by
# alphanumeric characters, underscores, or dots (for schema.table notation)
_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def validate_identifier(name: str) -> str:
    """Validate a SQL identifier (database name, schema name, table name).

    Only allows alphanumeric characters and underscores, starting with a
    letter or underscore. This prevents SQL injection through identifiers
    that cannot be parameterized (e.g., cross-database prefixes in MSSQL).

    Args:
        name: The identifier to validate.

    Returns:
        The validated identifier if safe.

    Raises:
        ValueError: If the identifier contains invalid characters.
    """
    if not name or not _IDENTIFIER_PATTERN.match(name):
        raise ValueError(
            f"Invalid SQL identifier: '{name}'. "
            "Only alphanumeric characters and underscores are allowed, "
            "starting with a letter or underscore."
        )
    return name


def validate_identifiers(names: List[str]) -> List[str]:
    """Validate a list of SQL identifiers.

    Args:
        names: List of identifiers to validate.

    Returns:
        List of validated identifiers.

    Raises:
        ValueError: If any identifier contains invalid characters.
    """
    return [validate_identifier(name) for name in names]


def build_in_params(
    param_prefix: str, values: List[str]
) -> Tuple[str, Dict[str, Any]]:
    """Build a parameterized IN clause with unique parameter names.

    Generates placeholders like (:p0, :p1, :p2) and a params dict
    mapping each placeholder name to its value.

    Args:
        param_prefix: Prefix for parameter names (e.g., "table_name").
        values: List of values for the IN clause.

    Returns:
        Tuple of (placeholder_string, params_dict).
    """
    if not values:
        return "('')", {}

    placeholders = []
    params: Dict[str, Any] = {}
    for i, value in enumerate(values):
        param_name = f"{param_prefix}_{i}"
        placeholders.append(f":{param_name}")
        params[param_name] = value

    return f"({', '.join(placeholders)})", params
