# Architecture

Comet Hunter is structured as a layered backend system centered around explicit state modeling and time-aware data flow.

The current focus is correctness and clarity rather than scale.

---

### Execution Flow

API Route
  → Pipeline
    → Service
      → Repository
        → SQLite

Services may additionally coordinate:
- remote HTTP retrieval
- file downloads
- image processing
- lifecycle recovery

### 1. API Layer

Responsible for external interaction with the system

Responsibilities:
- REST endpoints
- Request validation
- Response serialization
- Background job triggering
- Termination of inflight job
- Scheduler control

Examples:
- `/slots`
- `/frames`
- `/health`
- `/jobs`

The API layer contains no business logic and delegates orchestration to the pipeline layer

### 2. Pipeline Layer

Coordinates workflows across multiple services.

Responsibilities:
- Workflow orchestration
- Recovery corrdination
- Sequencing ingestion and processing stages
- Scheduler-driven execution

Examples:
- Live ingestion pipeline
- Observation-based synchronization pipeline

The Pipeline layer acts as a application orchestration boundary

### 3. Service Layer

Contains business workflows and lifecycle logic

Responsibilities:
- Slot synchronization
- Metadata Ingestion
- File Downloading
- File Processing

Characteristics:
- Explicit state-driven transitions
- Idempotent execution behaviour
- Recovery-oriented workflows

Services coordinate repositories and infrastructure operations while remaining persistence-aware but storage-agnostic.

### 4. Repository Layer

Responsibilities:
- Persistence (SQLite)
- Indexed queries
- Transaction boundaries

Characteristics:
- Transaction-scoped repository operations
- Explicit constraints
- Indexed timestamp columns
- Deterministic schema initialization

Repositories isolate storage concerns from workflow orchestration.

### 5. Domain Layer

Contains core entities and state definitions.

Examples:
- `DownlinkSlot`
- `FileMetadata`
- `ProcessedFile`

Characteristics:
- Enum-driven lifecycle states
- Explicit modeling of transitions

The domain layer contains no database or infrastructure logic.

### 6. Infrastructure Layer

Provides low-level operational capabilities used by higher layers:

Responsibilities:
- Database connectivity
- HTTP interaction
- File system access
- Image loading/saving
- Scheduler runtime integration

Examples:
- SQLite connection handling
- Remote metadata retrieval
- FITS file access
- APScheduler integration

Infrastructure components support higher layers without containing workflow logic.

---

### State-Driven Pipeline

The ingestion model progresses through explicit stages:

Slot lifecycle:
PENDING → ACTIVE → DONE / MISSED

File lifecycle (ideal):
DISCOVERED → DOWNLOADING → DOWNLOADED → READY → PROCESSING → PROCESSED
(with failure + retry branches)

Each transition is:

- Guarded by state checks
- Designed to be safely re-executable

This prevents duplicate downloads and inconsistent processing.

### Temporal Modeling

Time is treated as a primary dimension:

- Slots are indexed by expected timestamp
- Files are indexed by observation time
- Processed frames are retrieved chronologically

This aligns the database structure with the expected access pattern:
chronological playback.

### Design Priorities

- Deterministic lifecycle management
- Idempotent ingestion behavior
- Clear separation of concerns
- Reliable chronological retrieval
- Recovery-oriented execution

Horizontal scalability and distributed orchestration are intentionally out of scope at the current stage.