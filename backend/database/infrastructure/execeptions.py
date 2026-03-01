class DatabaseExecutionError(Exception):
    """
    Raised when a database query fails unexpectedly.

    Represents infrastructure-level failures such as:
    - SQL syntax errors
    - Constraint violations
    - Connection issues
    - Unexpected SQLite exceptions
    """
    pass