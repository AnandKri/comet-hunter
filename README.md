## Comet Hunter ( Work in Progress )

This project aims to help citizen scientists discover comets.

The intended end result is similar to [this output](https://soho.nascom.nasa.gov/data/LATEST/current_c3.gif) where processed images 
are compiled into a time-sequenced movie format, making faint sungrazing comets easier to detect than in individual frames.

You can refer to the [Sungrazer Project](https://sungrazer.nrl.navy.mil/) for more information.

---

### Project Design Principles

1. **Domain-Centric Architecture**  
Clear separation between domain, repository, and infrastructure layers, with explicit entity modeling and enum-driven state representation.

2. **Idempotent, State-Driven Pipeline**  
Incremental ingestion (slots → metadata → files) governed by explicit finite state transitions and safe retry logic.

3. **Scoped Consistency & Execution Model**  
Per-query transactional guarentees with no long-running transactions, and strict separation of database writes from network/file I/O.

4. **Relational Integrity, Performance & Observability**  
Normalized schema with constraints and indexing, structured logging at infrastructure boundaries and deterministic initialization.

---

### Definition of project being successful

At least one previously undiscovered comet is identified using this system.