# Comet Hunter (work in progress)

Comet Hunter is a deterministic ingestion and processing pipeline for LASCO image streams, designed to enable reliable visualization of faint moving sungrazing comets.

The project focuses on correctness, restartability, and explicit state modeling.

**Target outcome:**  
A structured backend system capable of ingesting, processing, and serving time-ordered frames for scientific inspection.

---

### Why This Exists

Present challenges:
- Images are required to be processed before they become usable
- Sungrazer comets are faint and often indistinguishable in single frame
- Chronological playback significantly improves detectability
- The citizen scientist community is large and highly active
- Most comets are reported within minutes of data availability.
- **Time is critical.**

The problem is not merely detection - it is **rapid** detection.

This requires automation with:
- Restartable ingestion
- Idempotent file acquisition
- State-consistent processing
- Time-indexed retrieval

This project approaches the problem as a reliability-focused systems design exercise.

---

### Running Locally

1. Initialize database
2. Sync slots
3. Sync metadata
4. Trigger download
5. Process files (in progress)
6. Visualization of processed files (planned)

(Commands and example script coming soon...)

---

### System Flow

1. Slot Modeling
2. File Metadata Ingestion  
4. File Discovery
5. File Download
6. File Processing  
7. Time-Indexed Retrieval  
8. Visualization Layer

Each stage is independently restartable and governed by explicit state transitions.

---

### Current Scope

Implemented:
- Domain entities
- Repository abstraction (SQLite)
- Deterministic schema bootstrap
- Enum-based finite state transitions
- Indexed temporal access patterns
- Metadata ingestion
- Download orchestration

In progress:
- Processing pipeline
- Implementing image processing algorithm

Planned:
- REST retrieval API
- Interactive chronological UI

---

### Architectural Characteristics

- Domain-first modeling
- Idempotent pipeline semantics (using file names as primary key, retry counters, state transitions)
- Explicit state transitions (no implicit flags)
- Per-query transactional boundaries
- Strict separation of DB writes from I/O
- Deterministic initialization
- Indexed time-series access
- Failure Handling (retry limits, failure states)

---

### Success Criteria

A fully restartable ingestion-to-visualization pipeline capable of surfacing at least one previously undetected comet.