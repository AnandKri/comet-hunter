from datetime import timedelta
from threading import Event
from backend.util.enums import Instrument, JobEventType
from backend.pipeline.pipeline import Pipeline
from backend.pipeline.models import SchedulerStartResult
from backend.jobs.exceptions import CancelledError
import logging

logger = logging.getLogger(__name__)

class Scheduler:
    """
    Runs live ingestion pipeline continously
    until explicitly stopped.
    """

    DEFAULT_INTERVAL_MINUTES = timedelta(minutes=5)

    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self.running = False
        
    def start(self, 
              instruments: list[Instrument], 
              cancel_event: Event, 
              job_id: str,
              job_type: str) -> SchedulerStartResult:
        """
        Starts the live ingestion pipeline for the given instruments.

        Notes:
        - Blocking method
        - Intended to run inside a background thread managed by BackgroundJobService
        
        """

        self.running = True

        logger.info(
            "Scheduler started",
            extra={"instruments": instruments}
        )

        try:
            while not cancel_event.is_set():

                next_run = self.DEFAULT_INTERVAL_MINUTES

                try:
                    if not instruments:
                        logger.warning("No instruments provided for scheduler run")
                        return SchedulerStartResult(
                            started=False,
                            running=self.running
                        )
                    
                    for instrument in instruments:
                        logger.info(
                            "Running ingestion cycle for instrument",
                            extra={"instrument": instrument}
                        )
                        result = self.pipeline.run_ingestion_cycle(instrument, cancel_event, job_id, job_type)

                        self.pipeline.publish_job_event(job_id, job_type, JobEventType.CYCLE_COMPLETED, {"next_run": str(result.next_run) if result.next_run else None})
                        logger.info(
                            "Ingestion cycle result",
                            extra={
                                "instrument": instrument,
                                "metadata_synced": result.metadata_synced,
                                "downloaded": result.downloaded,
                                "next_run": str(result.next_run) if result.next_run else None
                            }
                        )
                        if result.next_run:
                            next_run = result.next_run
                
                except CancelledError:
                    logger.info("Scheduler cycle execution cancelled")
                    raise
                except Exception:
                    logger.exception("Scheduler cycle execution failed")
                    raise
                
                logger.info(
                    "Scheduler waiting until next cycle run",
                    extra={"next_run": str(next_run) if next_run else None}
                )
                cancel_event.wait(next_run.total_seconds())
        
        finally:
            self.running = False
            logger.info("Scheduler stopped")
        
        return SchedulerStartResult(
            started=True,
            running=self.running
        )