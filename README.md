# Comet Hunter (work in progress)

Comet Hunter is a deterministic ingestion and processing pipeline for LASCO image streams, designed to enable reliable chronological visualization of faint moving sungrazing comets.

The project focuses on correctness, restartability, and explicit state modeling.

**Target outcome:**  
A structured backend system capable of ingesting, processing, and serving time-ordered frames for scientific inspection.

---

### Why This Exists

Present challenges:
- Raw images have low signal to noise ratio
- Images require preprocessed before they are usable
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

### System Flow

1. Slot Modeling
2. Metadata Detection  
3. File Registration  
4. File Download  
5. Frame Processing  
6. Time-Indexed Retrieval  
7. Visualization Layer

Each stage is independently restartable and governed by explicit state transitions.

---

### Current Scope

Implemented:
- Domain entities
- Repository abstraction (SQLite)
- Deterministic schema bootstrap
- Enum-based finite state transitions
- Indexed temporal access patterns

In progress:
- Metadata ingestion
- Download orchestration
- Processing pipeline

Planned:
- REST retrieval API
- Interactive chronological UI

---

### Architectural Characteristics

- Domain-first modeling
- Idempotent pipeline semantics
- Explicit state transitions (no implicit flags)
- Per-query transactional boundaries
- Strict separation of DB writes from I/O
- Deterministic initialization
- Indexed time-series access

---

### Success Criteria

A fully restartable ingestion-to-visualization pipeline capable of surfacing at least one previously undetected comet.