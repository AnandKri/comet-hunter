from datetime import datetime, UTC, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from typing import Optional
from threading import Lock, Thread
from backend.util.enums import Instrument
from backend.pipeline.pipeline import Pipeline
from backend.pipeline.models import SchedulerStatusResult, SchedulerStartResult, SchedulerStopResult

class Scheduler:
    """
    Runs only the live ingestion pipeline on a dynamic interval.
    """

    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self.scheduler = BackgroundScheduler(timezone=UTC)
        self.job_id = "run_live_pipeline_job"
        self.next_run_at: Optional[datetime] = None
        self.next_run_in: Optional[timedelta] = None
        self.running = False
        self._lock = Lock()

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
                result = self.pipeline.run_live_pipeline(instrument)
                next_run = result.next_run
            if not next_run:
                next_run = timedelta(minutes=5)
        except Exception as e:
            next_run = timedelta(minutes=5)

        self.next_run_in = next_run
        self.next_run_at = datetime.now(UTC) + next_run

        self.scheduler.add_job(
            self._job,
            trigger=DateTrigger(run_date=self.next_run_at),
            id=self.job_id,
            replace_existing=True,
            kwargs={"instruments": instruments}
        )

    def start(self, instruments: list[Instrument]) -> SchedulerStartResult:
        """
        Starts the scheduler and triggers the first pipeline execution.

        :param instruments: list of instruments for which job is to be ran
        
        Behavior:
        - Initializes and starts the APScheduler background scheduler
        - Immediately invokes `_job()` to kick off the pipeline without delay

        Notes:
        - Subsequent executions are handled by `_job()` via self-rescheduling
        - Should be called once during application startup
        """
        with self._lock:
            if self.running:
                return SchedulerStartResult(
                    started=False,
                    running=self.running
                )
            
            self.scheduler.start()
            self.running = True
            
            Thread(
                target=self._job,
                kwargs={"instruments": instruments},
                daemon=True
            ).start()

            return SchedulerStartResult(
                started=True,
                running=self.running
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

    def stop(self) -> SchedulerStopResult:
        """
        Stops the scheduler gracefully.

        Behavior:
        - Stops the APScheduler instance
        - Prevents any further scheduled executions

        Notes:
        - Should be called during application stop/cleanup
        - Ensures no background threads remain active
        """
        
        with self._lock:
            if not self.running:
                return SchedulerStopResult(
                    stopped=False,
                    running=self.running
                )
            
            self.scheduler.shutdown(wait=False)
            self.running = False
            self.next_run_at = None
            self.next_run_in = None
            
        return SchedulerStopResult(
            stopped=True,
            running=self.running
        )