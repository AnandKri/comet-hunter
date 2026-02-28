from dataclasses import dataclass
from typing import Optional, Any

@dataclass()
class QueryResult:
    """
    Standarized result returned by `QueryExecutor`

    Encapsulates execution outcome, optional result data,
    affected row count (specific to `write` operations),
    and error details

    Attributes:
        success: Indicates whether the query executed successfully
        rows_affected: number of rows modified (specific to `write` operations)
        data: fetched result set for `read` operations
        error_message: error description if execution failed.
    """
    
    success: bool
    rows_affected: int = 0
    data: Any = None
    error_message: Optional[str] = None