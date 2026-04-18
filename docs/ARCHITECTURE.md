# Architecture

Comet Hunter is structured as a layered backend system centered around explicit state modeling and time-aware data flow.

The current focus is correctness and clarity rather than scale.

---

### 1. Domain Layer

Contains core entities and state definitions.

Examples:
- DownlinkSlot
- FileMetadata
- ProcessedFile

Characteristics:
- No direct database logic
- Enum-driven lifecycle states
- Explicit modeling of transitions

The goal is to make state progression visible and predictable.

---

### 2. Repository Layer

Responsible for:

- Persistence (SQLite)
- Indexed queries
- Transaction boundaries

Design decisions:
- Per-operation transactions
- Explicit constraints
- Indexed timestamp columns
- Deterministic schema initialization

The repository layer abstracts storage concerns from domain logic.

---

### 3. Infrastructure Layer

Handles:

- Remote metadata retrieval
- File downloading
- Local file management
- Frame processing

Database updates are intentionally separated from network and file I/O operations to reduce side-effect coupling.

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

---

### Temporal Modeling

Time is treated as a primary dimension:

- Slots are indexed by expected timestamp
- Files are indexed by observation time
- Processed frames are retrieved chronologically

This aligns the database structure with the expected access pattern:
chronological playback.

---

### Current Focus

- Clear separation of concerns
- Explicit lifecycle modeling
- Idempotent ingestion behavior
- Reliable chronological retrieval

Scaling and distributed concerns are out of scope at this stage.