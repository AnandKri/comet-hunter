# Contributing to Comet Hunter

## Overview

This project follows a structured backend architecture focused on reliability, idempotency, and clean separation of concerns. Contributions are expected to align with these principles.

---

## Setup Instructions (based on current state)

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Initialize the database:

```
python -c "from backend.database.infrastructure.bootstrap import bootstrap_database; bootstrap_database()"
```

This sets up all required tables and indexes.

---

## Project Architecture

The codebase is organized into distinct layers:

* **domain/**
  Immutable entities representing core business objects (e.g., ProcessedFile, DownlinkSlot)

* **repositories/**
  Database interaction layer. All SQL must live here.

* **services/**
  Business logic and workflows (slot syncing, metadata ingestion, file processing)

* **infrastructure/**
  Low-level database execution and query handling

---

## Core Design Principles

* Domain entities are **immutable**
  Use controlled transitions (`transition_to`) or `replace()` patterns

* Follow **strict separation of concerns**

  * No SQL inside services
  * No business logic inside repositories

* Maintain **idempotent workflows**
  Re-running operations should not create duplicates or inconsistent state

* Use **Enums for all state management**
  Avoid raw strings for statuses

---

## Contribution Workflow

1. Fork the repository
2. Create a new branch, based on feature/fix

   ```
   git checkout -b feat/your-feature-name
   ```
   ```
   git checkout -b fix/your-fix-name
   ```
3. Make your changes
4. Ensure code follows project structure and rules
5. Commit with clear messages
6. Open a Pull Request with:

   * Description of changes
   * Reason for change
   * Any assumptions or trade-offs

---

## Coding Guidelines

* Keep functions small and focused
* Prefer readability over cleverness
* Use type hints in function definitions
* Add docstring for each function
* Follow existing naming conventions
* Reuse existing abstractions instead of introducing new ones unnecessarily
* AI generated code should be reviewed thoroughly, line-by-line

---

## Database Guidelines

* All database access must go through repositories
* Use `QuerySpec` and `QueryExecutor` for all queries
* Do not write raw SQL outside repository classes
* Maintain schema consistency and indexing strategy

---

## File Processing Rules

* Respect lifecycle transitions defined in domain models
* Do not bypass state transitions
* Ensure retry logic respects attempt limits
* Preserve traceability via timestamps and error messages

---

## What Not To Do

* Do not mutate domain objects directly
* Do not introduce tight coupling between services
* Do not bypass repositories for quick fixes
* Do not change schema without proper discussion
* Do not ignore failure states or error handling

---

## Reporting Issues

When reporting a bug, include:

* Clear description of the issue
* Steps to reproduce
* Relevant logs or error messages
* Expected vs actual behavior

---

## Suggested Areas for Contribution

* Download and processing performance improvements
* Better algorithm to process FTS images
* Retry and failure handling enhancements
* Metadata parsing robustness
* UI or visualization layer for processed images
* Observability (logging, metrics)

---

## Final Notes

Consistency matters more than speed.
Maintain the architecture. Avoid shortcuts.
Every contribution should improve clarity, reliability, or extensibility of the system.
