# Roadmap

The roadmap is organized around system maturity rather than feature breadth.

---

### Phase 1 — Deterministic Core (Implemented)

- Domain modeling
- Enum-based state transitions
- Repository abstraction
- Indexed schema bootstrap
- Slot lifecycle enforcement

**Goal:**  
Establish a restartable, correct ingestion skeleton.

---

### Phase 2 — Metadata & Download Integrity (Implemented)

- Remote metadata polling
- Unique file discovery
- Download orchestration (implemented, in testing)
- Retry semantics
- Local file structure normalization

**Goal:**  
Achieve deterministic, idempotent file acquisition.

---

### Phase 3 — Processing Pipeline (Implemented)

- FITS ingestion
- Frame normalization
- Contrast enhancement
- Frame differencing (core of motion detection)
- Processed output tracking

**Goal:**  
Produce consistent, time-aligned frames.

---

### Phase 4 — Retrieval API (In Progress)

- Time-sorted retrieval endpoints
- Pagination
- Metadata filtering
- Observability instrumentation

**Goal:**  
Enable reliable chronological inspection.

---

### Phase 5 — Visualization Layer

- Frame playback
- Timeline scrubbing
- Adjustable playback speed
- Metadata inspection

**Goal:**  
Enable human detection of faint motion patterns.

---

### Phase 6 — Hardening

- Performance benchmarking
- Concurrency validation
- Failure injection testing
- Storage optimization
- Archival policies

**Goal:**  
Ensure robustness under extended operation.

---

### Long-Term Direction

If validated:

- Parallelized processing (Implemented)
- Automated motion detection (heavier lift)
- Statistical and classical machine learning methods for candidate identification