# QueryExecutor

Centralized query execution layer.

Responsible for:

- validating SQL operation semantics
- executing parameterized queries
- transaction management
- normalizing database responses
- raising infrastructure-level exceptions

## Notes

- READ operations must use SELECT
- WRITE operations cannot use SELECT
- Batch operations use `execute_many`

::: backend.database.infrastructure.query_executor.QueryExecutor