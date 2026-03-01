from dataclasses import dataclass
from typing import Any

@dataclass()
class QueryResult:
    """
    Standarized result returned by `QueryExecutor`

    Encapsulates optional result data and affected 
    row count (specific to `write` operations)

    Attributes:
        rows_affected: number of rows modified (specific to `write` operations)
        data: fetched result set for `read` operations
    """
    
    rows_affected: int = 0
    data: Any = None