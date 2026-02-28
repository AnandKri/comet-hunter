from dataclasses import dataclass
from typing import Sequence, Optional, Any
from backend.util.enums import OperationType, FetchType

@dataclass(frozen=True)
class QuerySpec:
    """
    Immutable specification of a database query.

    Encapsulates the sql string, its operation type, bound parameters,
    and expected fetch behaviour. Designed to decouple query definition
    from execution logic inside repositories.

    Attributes:
        sql: parameterized SQL statement
        operation: type of database operations (`read` or `write`)
        params: positional parameters bound to the SQL statement.
        fetch: Fetch strategy, defined only for `read` operations (`one` or `all`)
    
    Invariants:
        - READ operations must define fetch type
        - WRITE operations cannot have a fetch type  
    """
    sql: str
    operation: OperationType
    params: Sequence[Any] = ()
    fetch: Optional[FetchType] = None

    def __post_init__(self):

        if self.operation is OperationType.READ and self.fetch is None:
            raise ValueError("Read operations must define fetch")
        
        if self.operation is OperationType.WRITE and self.fetch is not None:
            raise ValueError("Write operations cannot define fetch.")