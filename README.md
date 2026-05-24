# Comet Hunter

Comet Hunter is a tool which helps in discovering comets.

## About The Project

NASA's [Sungrazer Project](https://www.esa.int/Science_Exploration/Space_Science/Sungrazer_comets) enables the discovery and reporting of comets visible from the SOHO and STEREO satellites. To date, over five thousand comets have been discovered using the SOHO satellite. On board SOHO is the LASCO coronagraph, which consists of two telescopes — C2 and C3. Images from these telescopes are primarily used for reporting new comets.

For comet discovery, users rely on commercially available tools or software to streamline parts of the workflow or assist in identifying potential comets. However, there is no single platform that streamlines the end-to-end comet hunting process. **Comet Hunter is created with the aim of helping bridge this gap**.

### Why This Exists?

**Present challenges**:
- RAW images are required to be processed before they become usable
- Sungrazer comets are faint and often indistinguishable in single frame
- Chronological playback of images significantly improves detectability
- The citizen scientist community is large and highly active
- Most comets are reported within minutes of data availability.
- **Time is critical.**

The problem is not merely detection - it is **rapid** detection. 

This requires a **robust automation** of the end-to-end process right from getting the RAW images to the chronological playback of processed images. And Comet Hunter does exactly this.

## Getting Started

### Running Locally

1. Initialize database
2. Sync slots
3. Sync metadata
4. Trigger download
5. Process files
6. Visualization of processed files (planned)

(Commands and example script coming soon...)

### Documentation

Complete project documentation can be found at [Comet Hunter](https://anandkri.github.io/comet-hunter/).

### System Flow

1. Slot Modeling  
2. File Metadata Ingestion  
4. File Discovery and Download  
5. File Processing  
6. Time-Indexed Retrieval  
7. Visualization Layer

Each stage is independently restartable and governed by explicit state transitions.

### Current Scope

Implemented:
- Domain entities
- Repository abstraction (SQLite)
- Deterministic schema bootstrap
- Enum-based finite state transitions
- Indexed temporal access patterns
- Metadata ingestion
- Download orchestration
- Processing pipeline
- Image processing algorithm
- REST retrieval API
- Logging configuration

In progress:
- Background Job cancellation
- Establishing Server-Sent Events
- Interactive UI

### Architectural Characteristics

- Domain-driven architecture
- Idempotent ingestion and processing pipeline
- Explicit lifecycle state machines
- Transaction-scoped database operations
- Separation of persistence and external I/O
- Deterministic service initialization
- Indexed time-based querying
- Built-in retry and failure recovery mechanisms
- Immutable domain entities
- Repository-service architectural pattern
- Concurrent download and processing workflows
- Dynamic scheduler-driven pipeline execution