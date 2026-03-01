# Roadmap

The roadmap is organized around system maturity rather than feature breadth.

---

### Phase 1 — Deterministic Core (In Progress)

- Domain modeling
- Enum-based state transitions
- Repository abstraction
- Indexed schema bootstrap
- Slot lifecycle enforcement

**Goal:**  
Establish a restartable, correct ingestion skeleton.

---

### Phase 2 — Metadata & Download Integrity

- Remote metadata polling
- Unique file registration
- Download orchestration
- Retry semantics
- Local file structure normalization

**Goal:**  
Achieve deterministic, idempotent file acquisition.

---

### Phase 3 — Processing Pipeline

- FITS ingestion
- Frame normalization
- Contrast enhancement
- Optional differencing
- Processed output tracking

**Goal:**  
Produce consistent, time-aligned frames.

---

### Phase 4 — Retrieval API

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

- Parallelized processing
- Distributed ingestion
- Automated motion detection heuristics
- Statistical filtering for candidate identification