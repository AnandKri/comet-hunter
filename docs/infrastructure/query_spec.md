# QuerySpec

Immutable query specification object used by repositories.

Encapsulates:

- SQL statement
- operation type
- parameters
- fetch strategy

## Design Goals

- decouple query definition from execution
- enforce query invariants
- standardize repository behavior

::: backend.database.infrastructure.query_spec.QuerySpec