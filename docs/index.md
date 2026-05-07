# Comet Hunter

Comet Hunter is a modular data pipeline for ingesting, tracking, downloading, and processing LASCO coronagraph imagery from the SOHO mission.

The system is designed around reliability, deterministic state transitions, and idempotent execution for long-running astronomical data workflows.

---

## Core Capabilities

- Synchronization of LASCO metadata and downlink schedules
- Automated FITS file discovery and downloading
- Image processing for:
  - **C2** → unsharp masking
  - **C3** → running difference
- Persistent lifecycle tracking using SQLite
- Concurrent download and processing execution
- Retry-safe and recovery-oriented workflows

---

## Pipeline Overview

```text
Downlink Slots
       ↓
Metadata Synchronization
       ↓
File Discovery
       ↓
FITS Download
       ↓
READY State Resolution
       ↓
Image Processing
       ↓
Processed Outputs
```

---

## Architecture

The project follows a layered architecture with clear separation of concerns:

```text
Domain
  ↓
Repositories
  ↓
Services
  ↓
Infrastructure
```

### Layers

| Layer | Responsibility |
|---|---|
| Domain | Immutable business entities and lifecycle rules |
| Repository | SQLite persistence and query abstraction |
| Service | Pipeline orchestration and workflow execution |
| Infrastructure | Database connection and execution layer |

---

## Processing Lifecycle

Files move through a deterministic lifecycle:

```text
DISCOVERED
    ↓
DOWNLOADING
    ↓
DOWNLOADED
    ↓
READY
    ↓
PROCESSING
    ↓
PROCESSED
```

Recovery and retry states are also supported for fault tolerance and resumability.

---

## Key Design Principles

- **Idempotent execution**
  - Re-running workflows does not duplicate processing.

- **State-driven orchestration**
  - File transitions are strictly controlled through lifecycle rules.

- **Recovery-oriented workflows**
  - Stale downloads and processing tasks can be recovered safely.

- **Concurrent execution**
  - Parallel downloading and processing using worker pools.

- **Repository abstraction**
  - Database access is centralized through query specifications and executors.

---

## Technologies

- Python
- SQLite
- FastAPI

---

## Project Goals

Comet Hunter is intended to serve as:

- A production-style astronomical data pipeline
- A reliable FITS ingestion and processing framework
- A foundation for future comet detection and analysis workflows
- A reference implementation for state-driven scientific processing systems