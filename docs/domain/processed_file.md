# ProcessedFile

`ProcessedFile` is the central lifecycle entity responsible for tracking
the complete state evolution of LASCO image files throughout the pipeline.

It models:

- raw file discovery
- downloading
- processing readiness
- image processing execution
- retry handling
- terminal completion states

---

## Responsibilities

The entity maintains lifecycle consistency for:

- raw FITS files
- processed image outputs
- retry attempts
- processing timestamps
- failure recovery
- predecessor relationships (C3 running difference)

---

## Lifecycle Diagram

![Processed File Lifecycle](../lifecycle/processed_file_lifecycle.svg)

---

## Core Guarantees

### Immutable Transitions

All lifecycle transitions return a new immutable entity instance.

This prevents accidental mutation and ensures predictable state evolution.

### Retry-Safe Processing

The entity explicitly tracks:

- download retry count
- processing retry count
- last retry timestamps

This allows recovery-oriented workflows without duplicating work.

### Terminal State Enforcement

Terminal states prevent further transitions once processing is complete
or permanently abandoned.

Terminal states include:

- `PROCESSED`
- `SKIPPED`
- `IGNORE`
- `ABANDONED`

---

## State Categories

| Category | States |
|---|---|
| Discovery | `DISCOVERED` |
| Downloading | `DOWNLOADING`, `DOWNLOADED`, `DOWNLOADING_FAILED` |
| Processing Preparation | `READY` |
| Processing | `PROCESSING`, `PROCESSED`, `PROCESSING_FAILED` |
| Terminal | `SKIPPED`, `IGNORE`, `ABANDONED` |

---

## C3 Processing Relationship

For LASCO C3 processing, the entity also stores:

- `previous_file_name`

This enables running-difference processing between sequential observations.

---

## Design Notes

The lifecycle model is intentionally deterministic and state-driven.

The processing pipeline never infers workflow state from filesystem
conditions alone — all orchestration decisions are derived from
persisted lifecycle state.

This provides:

- resumability
- idempotent execution
- crash recovery
- workflow observability

---

## API Reference

::: backend.database.domain.processed_file.ProcessedFile