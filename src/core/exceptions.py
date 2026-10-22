class DataSourcePermissionError(Exception):
    """Data source permission error.

    Raised when a role lacks permission for the requested operation.
    Applies to all paradigms (SQL, Redis, MongoDB, etc.).
    """
    pass


# Backward compatibility alias.
# Code that still references SQLPermissionError will continue to work.
SQLPermissionError = DataSourcePermissionError


class SQLExecutionError(Exception):
    """SQL execution error"""
    pass
