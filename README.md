# Comet Hunter

Comet Hunter is an automated astronomical image ingestion and processing system designed to assist in the discovery of sungrazing comets from SOHO LASCO imagery.

## About The Project

NASA's [Sungrazer Project](https://sungrazer.nrl.navy.mil/) enables the discovery and reporting of comets visible from the SOHO and STEREO satellites. To date, over five thousand comets have been discovered using the SOHO satellite. On board SOHO is the LASCO coronagraph, which consists of two telescopes — C2 and C3. Images from these telescopes are primarily used for reporting new comets.

### Why This Exists?

For comet discovery, users rely on fragmented tools for downloading, processing, and reviewing imagery. There is no unified platform that automates the complete workflow from raw image availability to chronological playback of processed frames. **Comet Hunter aims to bridge this gap**.

### Present Challenges
- RAW images must be processed before becoming usable
- Sungrazer comets are often indistinguishable in single frames
- Chronological playback significantly improves detectability
- Most comets are reported within minutes of data availability.
- **Time is critical.**

The problem is not merely detection - it is **rapid** detection. 

This requires a **robust automation** of the complete workflow: from RAW image ingestion to chronological playback of processed frames.

## Current Capabilities

- Downlink slot synchronization
- Metadata ingestion from LASCO sources
- Parallel RAW image downloading
- Image processing pipelines for C2/C3
- Time-indexed frame retrieval
- REST API backend
- Scheduler-driver ingestion workflows
- Interactive frontend visualization

## Getting Started

### Clone Repository

```bash
git clone https://github.com/AnandKri/comet-hunter.git
cd comet-hunter
```

### Create Virtual Environment

**Linux/macOS**

```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install requirement.txt
```

### Run Backend

```bash
uvicorn backend.main:app --reload
```

### Run Frontend

```bash
python frontend/app.py
```

## Documentation

<a href="https://anandkri.github.io/comet-hunter/" target="_blank">
View Full Documentation
</a>