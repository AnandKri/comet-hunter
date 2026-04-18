# Database Schema

This document defines the relational schema used in Comet Hunter.  
The system is built on SQLite with a focus on deterministic behavior, idempotent ingestion, and efficient time-based querying.

---

## Tables Overview

| Table Name        | Purpose |
|------------------|--------|
| `downlink_slot`  | Tracks scheduled communication windows for data availability |
| `file_metadata`  | Stores metadata of available LASCO files (from C2 and C3 coronagraphs) |
| `processed_file` | Tracks lifecycle of each file through ingestion and processing |


---  

## 1. downlink_slot

Represents scheduled downlink windows during which image data is expected.

### Schema

```sql
CREATE TABLE downlink_slot (
    wk INTEGER NOT NULL,
    doy INTEGER NOT NULL,
    wdy TEXT NOT NULL,
    bot_utc TEXT NOT NULL,
    eot_utc TEXT NOT NULL,
    ant TEXT,
    status TEXT NOT NULL CHECK(status IN ('MISSED','PENDING','ACTIVE','DONE')),
    PRIMARY KEY (wk, doy, wdy, bot_utc)
);
```

### Indexes

```sql
CREATE INDEX idx_schedule_status_time
ON downlink_slot (status, bot_utc)
```

### Notes

- Composite primary key ensures uniqueness per slot
- `bot_utc` and `eot_utc` are stored in ISO 8601 UTC format
- Status lifecycle (ideal): PENDING → ACTIVE → DONE
- Indexed for fast retrieval of active and upcoming slots

---

## 2. file_metadata

Stores metadata parsed from LASCO sources before file download

### Schema

```sql
CREATE TABLE file_metadata (
    raw_file_name TEXT PRIMARY KEY,
    raw_file_hash TEXT,
    datetime_of_observation TEXT NOT NULL,
    last_modified_utc TEXT NOT NULL,
    instrument TEXT NOT NULL,
    exposure_time REAL NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    roll REAL NOT NULL
);
```

### Indexes

```sql
CREATE INDEX idx_file_metadata_observation_time
ON file_metadata (instrument, datetime_of_observation);

CREATE INDEX idx_file_metadata_modified_time
ON file_metadata (instrument, last_modified_utc);

CREATE INDEX idx_file_metadata_name
ON file_metadata (raw_file_name);
```

### Notes

- `raw_file_name` is the identifier
- `last_modified_utc` is used only for ingestion
- `datetime_of_observation` is used for chronological playback
- `instrument` values: `C2`,`C3`
- Hash values are optional and maybe populated later

---

## 3. processed_file

Tracks full lifecycle of a file from discovery to processing

### Schema

```sql
CREATE TABLE processed_file (
    raw_file_name TEXT PRIMARY KEY,
    raw_file_hash TEXT UNIQUE,
    raw_file_path TEXT UNIQUE NOT NULL,
    raw_file_size INTEGER,

    processed_file_name TEXT UNIQUE,
    processed_file_hash TEXT UNIQUE,
    processed_file_path TEXT UNIQUE,
    processed_file_size INTEGER,

    datetime_of_observation TEXT NOT NULL,
    instrument TEXT NOT NULL,
    status TEXT NOT NULL,

    error_message TEXT,

    downloaded_at TEXT,
    last_downloading_attempt_at TEXT,
    downloading_attempt_count INTEGER NOT NULL DEFAULT 0,

    processed_at TEXT,
    last_processing_attempt_at TEXT,
    processing_attempt_count INTEGER NOT NULL DEFAULT 0
);
```

### Indexes

```sql
CREATE INDEX idx_processed_status_time
ON processed_file (status, datetime_of_observation);
```

### Notes

- `raw_file_name` is the primary key
- Separate tracking for download and processing retries
- Immutable state transitions enforced at domain level
- Supports idempotent re-execution
- Find detailed of State lifecycle [here](lifecycle//processed_file_lifecycle.svg)