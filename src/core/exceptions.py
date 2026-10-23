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


class ConfigurationError(ValueError):
    """Configuration error.

    Raised when the database/pool configuration is invalid (e.g. an
    unknown role, a missing mandatory ``default`` pool, or an unknown
    pool name). The system fails closed rather than silently guessing.
    """
    pass
