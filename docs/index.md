# Comet Hunter

**Comet Hunter** is a tool to help citizen scientists discover [sungrazing comets](https://www.esa.int/Science_Exploration/Space_Science/Sungrazer_comets).  

The project serves as an engineering exercise in building fault-tolerant data pipelines, immutable state-driven workflows, and recovery-oriented backend systems.

It explores scientific computing, concurrent processing, and orchestration patterns in a real-world observational data context.

## Context & Inspiration

NASA's Sungrazer Project enables the discovery and reporting of comets visible from the SOHO and STEREO satellites. To date, over **5000** comets have been discovered using the SOHO satellite. On board SOHO is the LASCO coronagraph, which consists of two telescopes — **C2** and **C3**. Images from these telescopes are primarily used for reporting new comets.

For comet discovery, users may rely on commercially available tools or software to streamline parts of the workflow or assist in identifying potential comets. However, there is no single platform that streamlines the end-to-end comet hunting process. **Comet Hunter** was created with the aim of helping bridge this gap.

## Core Capabilities

- Synchronization of LASCO metadata and downlink schedules
- Automated FITS file discovery and downloading
- Image processing algorithm for:
  - **C2** : Unsharp masking
  - **C3** : Running difference
- Persistent lifecycle tracking using SQLite
- Concurrent download and processing execution
- Retry-safe and recovery-oriented workflows

## Pipeline Overview

```text
Downlink Slots
       ↓
Metadata Synchronization
       ↓
File Discovery and Download
       ↓
READY State Resolution
       ↓
Image Processing
       ↓
Visualization of Processed Outputs
```

## Architecture

The project follows a layered architecture with clear separation of concerns:

```text
API
  ↓
Pipeline
  ↓
Services
  ↓
Repositories
  ↓
Infrastructure
```

`Domain` entities are shared across services and repositories.


### Layers

| Layer | Responsibility |
|---|---|
| API | Entry points for triggering synchronization and processing workflows |
| Pipeline | Coordinates end-to-end execution across ingestion, download, and processing stages |
| Service | Encapsulates business workflows, lifecycle transitions, and recovery logic |
| Repository | Handles SQLite persistence, query abstraction, and state retrieval |
| Infrastructure | Provides low-level database connection and query execution mechanisms |
| Domain | Immutable entities and deterministic lifecycle/state transition rules shared across layers |

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

## Key Design Principles

- **Idempotent execution** : Re-running workflows does not duplicate processing.

- **State-driven orchestration** : File transitions are strictly controlled through lifecycle rules.

- **Recovery-oriented workflows** : Stale downloads and processing tasks can be recovered safely.

- **Concurrent execution** : Parallel downloading and processing using worker pools.

- **Repository abstraction** : Database access is centralized through query specifications and executors.

## Engineering Principles

The project emphasizes modular architecture, deterministic workflows, immutable domain modeling, explicit lifecycle management, and recovery-oriented pipeline design.

Additional focus is placed on observability, maintainability, and operational resilience.

## Technologies

### Backend & API
- Python
- FastAPI

### Database & Persistence
- SQLite
- WAL journaling

### Scientific Computing & Image Processing
- NumPy
- SciPy
- SunPy
- Matplotlib

### Architecture & Tooling
- Repository-Service-Domain architecture
- Immutable dataclass-based domain modeling
- Concurrent execution with ThreadPoolExecutor

## Project Goals

Comet Hunter is intended to serve as:

- A production-oriented scientific data pipeline emphasizing deterministic lifecycle management and recovery-safe workflows
- An exploration of fault-tolerant backend architecture using lightweight infrastructure and modular system design
- A foundation for future comet detection, temporal image analysis, and automated observational workflows
- A reference implementation for state-driven orchestration, scientific image processing, and resilient ingestion systems