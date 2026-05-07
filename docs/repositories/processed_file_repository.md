# ProcessedFileRepository

Repository responsible for tracking file lifecycle state
through downloading and processing stages.

## Responsibilities

- Persist ProcessedFile entities
- Update lifecycle states
- Query retryable files
- Track processed outputs

## Lifecycle States

- DISCOVERED
- DOWNLOADING
- DOWNLOADED
- READY
- PROCESSING
- PROCESSED
- FAILED states

## API Reference

::: backend.database.repositories.processed_file_repository.ProcessedFileRepository