from datetime import datetime, UTC, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import logging

from backend.util.enums import Instrument
from backend.pipeline.pipeline import Pipeline


logger = logging.getLogger(__name__)


class Scheduler:
    """
    Runs only the live ingestion pipeline on a fixed interval.
    """

    def __init__(self, pipeline: Pipeline, instruments: list[Instrument]):
        self.pipeline = pipeline
        self.instruments = instruments
        self.scheduler = BackgroundScheduler(timezone=UTC)

    def _job(self):
        """
        Executes one cycle of the live ingestion pipeline and schedules the next run.

        Workflow:
        - Triggers `pipeline.run_live_pipeline()` for the configured instrument/s
        - Logs key metrics (metadata synced, files downloaded, next run interval)
        - Determines next execution time based on returned `next_run` timedelta
        - Falls back to a default interval if execution fails or `next_run` is None
        - Schedules the next execution using a one-shot (DateTrigger) job

        Notes:
        - This method is self-rescheduling (no fixed interval loop)
        - Only pipeline execution is wrapped in error handling; scheduling is not
        
        """
        try:
            for instrument in self.instruments:
                logger.info(f"instrument : {Instrument.value}")
                
                result = self.pipeline.run_live_pipeline(instrument)

                logger.info(f"  metadata_synced : {result.metadata_synced}")
                logger.info(f"  downloaded : {result.downloaded}")
                logger.info(f"  next_run : {result.next_run}")
            
                next_run = result.next_run
        
        except Exception as e:
            logger.exception(f"Scheduler job failed: {e}")
            next_run = timedelta(minutes=5)

        next_time = datetime.now(UTC) + next_run

        self.scheduler.add_job(
            self._job,
            trigger=DateTrigger(run_date=next_time),
            id="run_live_pipeline_job",
            replace_existing=True,
        )

    def start(self):
        """
        Starts the scheduler and triggers the first pipeline execution.

        Behavior:
        - Initializes and starts the APScheduler background scheduler
        - Immediately invokes `_job()` to kick off the pipeline without delay

        Notes:
        - Subsequent executions are handled by `_job()` via self-rescheduling
        - Should be called once during application startup
        """
        self.scheduler.start()
        self._job()

    def shutdown(self):
        """
        Stops the scheduler gracefully.

        Behavior:
        - Shuts down the APScheduler instance
        - Prevents any further scheduled executions

        Notes:
        - Should be called during application shutdown/cleanup
        - Ensures no background threads remain active
        """
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")