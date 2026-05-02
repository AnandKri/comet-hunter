from datetime import datetime, UTC, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import logging
from typing import Optional
from backend.util.enums import Instrument
from backend.pipeline.pipeline import Pipeline
from backend.pipeline.models import SchedulerStatusResult, SchedulerStartResult, SchedulerShutdownResult

logger = logging.getLogger(__name__)


class Scheduler:
    """
    Runs only the live ingestion pipeline on a fixed interval.
    """

    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self.scheduler = BackgroundScheduler(timezone=UTC)
        self.job_id = "run_live_pipeline_job"
        self.next_run_at: Optional[datetime] = None
        self.next_run_in: Optional[timedelta] = None
        self.running = False

    def _job(self, instruments: list[Instrument]):
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
            for instrument in instruments:
                logger.info(f"instrument : {Instrument.value}")
                
                result = self.pipeline.run_live_pipeline(instrument)

                logger.info(f"  metadata_synced : {result.metadata_synced}")
                logger.info(f"  downloaded : {result.downloaded}")
                logger.info(f"  next_run : {result.next_run}")
            
                next_run = result.next_run
        
        except Exception as e:
            logger.exception(f"Scheduler job failed: {e}")
            next_run = timedelta(minutes=5)

        self.next_run_in = next_run
        self.next_run_at = datetime.now(UTC) + next_run

        self.scheduler.add_job(
            self._job,
            trigger=DateTrigger(run_date=self.next_run_at),
            id=self.job_id,
            replace_existing=True,
        )

    def start(self, instruments: list[Instrument]) -> SchedulerStartResult:
        """
        Starts the scheduler and triggers the first pipeline execution.

        :param instruments: list of instruments for which job is to be ran
        :return: 0 on successful execution

        Behavior:
        - Initializes and starts the APScheduler background scheduler
        - Immediately invokes `_job()` to kick off the pipeline without delay

        Notes:
        - Subsequent executions are handled by `_job()` via self-rescheduling
        - Should be called once during application startup
        """
        if not self.running:
            self.scheduler.start()
            self.running = True
            self._job(instruments)
        
        return SchedulerStartResult(
            response=0
        )
    
    def get_status(self) -> SchedulerStatusResult:
        """
        Returns scheduler state.

        :return: dataclass entity with running state
        next run time and time remaining in next run
        """
        return SchedulerStatusResult(
            self.running,
            self.next_run_at,
            self.next_run_in
        )

    def shutdown(self) -> SchedulerShutdownResult:
        """
        Stops the scheduler gracefully.

        Behavior:
        - Shuts down the APScheduler instance
        - Prevents any further scheduled executions

        Notes:
        - Should be called during application shutdown/cleanup
        - Ensures no background threads remain active
        """
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            self.next_run_at = None
            self.next_run_in = None
            logger.info("Scheduler stopped")
        return SchedulerShutdownResult(
            response=0
        )