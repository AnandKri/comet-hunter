class DatabaseExecutionError(Exception):
    """
    Raised when a database query fails unexpectedly.

    Represents infrastructure-level failures such as:
    - SQL syntax errors
    - Constraint violations
    - Connection issues
    - Unexpected SQLite exceptions
    """
    def __init__(self, message: str, query: str = None, params=None):
        super().__init__(message)
        self.query = query
        self.params = params