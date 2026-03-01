from query_spec import QuerySpec
from query_result import QueryResult
from base import DatabaseBase
from backend.util.enums import FetchType, OperationType
import logging
from execeptions import DatabaseExecutionError

logger = logging.getLogger(__name__)

class QueryExecutor:
    """
    Centralized database query execution layer.
    
    Responsible for:
        - Validating operation type against SQL statement semantics
        - Managing transaction boundaries (commit/rollback)
        - Executeing parameterized queries
        - Normalizing database responses into `QueryResult`
        - raising and logging execution failures
    
    Acts as the single boundary between repositories and the 
    underlying database connection
    """
    
    def execute(self, query: QuerySpec) -> QueryResult:
        try:

            sql_upper = query.sql.strip().upper()

            if query.operation is OperationType.READ and not sql_upper.startswith("SELECT"):
                raise ValueError("Read operation must use SELECT statement.")

            if query.operation is OperationType.WRITE and sql_upper.startswith("SELECT"):
                raise ValueError("Write operation cannot use SELECT statement.")

            with DatabaseBase.get_connection() as conn:
                cursor = conn.execute(query.sql, query.params)

                if query.operation is OperationType.READ:
                    if query.fetch is FetchType.ONE:
                        row = cursor.fetchone()
                        return QueryResult(
                            data=row
                        )
                    elif query.fetch is FetchType.ALL:
                        rows = cursor.fetchall()
                        return QueryResult(
                            data=rows
                        )
                else:
                    return QueryResult(
                        affected_rows=cursor.rowcount
                    )
        except Exception as e:
            logger.exception("Database query failed")
            raise DatabaseExecutionError(str(e)) from e