from collections import defaultdict
from queue import Queue
from backend.jobs.event_models import JobEvent

class EventBus:
    """
    Lightweight in-memory event bus for publishing
    job-specific realtime events.

    Responsibilities:
    - maintain subscribers grouped by job_id
    - Allow publishers to emit events
    - Allow SSE consumers to subscribe
    - Fan-out events to all active subscribers

    Notes:
    - Thread-safe enough for lightweight usage because Queue is thread-safe
    - In-memory only
    - Subscribers are lost on process restart
    - Intended for single-instance deployment
    """

    def __init__(self) -> None:
        """
        Initialize subscribers registry.

        Struture:
            {
                job_id: [Queue(), Queue(), ...]
            }
        
        Each Queue belong to one connected SSE client.
        """

        self._subscribers = defaultdict(list)
    
    def publish(self, job_id: str, event: JobEvent) -> None:
        """
        Publish event to all subscribers listening to the given job.

        Workflow:
        - Find all subscriber queue for job_id
        - Push event into each queue

        :param job_id:
            Unique job identifier
        
        :param event:
            JobEvent instance representing a event payload
        """

        queues = self._subscribers.get(job_id, [])

        for queue in queues:
            queue.put(event)
    
    def subscribe(self, job_id: str) -> Queue:
        """
        Register a new subscriber for a job stream.

        Creates:
        - dedicated Queue for a subcriber

        Workflow:
        - Create queue
        - Store queue under job_id
        - Return queue to caller

        :param job_id:
            Unique job identifier
        
        :return:
            Subscriber queue
        """

        queue = Queue()

        self._subscribers[job_id].append(queue)

        return queue
    
    def unsubscribe(self, job_id: str, queue: Queue) -> None:
        """
        Remove subscriber queue from the job stream.

        Called when:
        - SSE client disconnects
        - Job completion
        - request terminates
        - cleanup occurs

        Workflow:
        - Remove queue from subscriber list
        - Cleanup empty job bucket

        :param job_id:
            Unique job identifier
        
        :param queue:
            Subscriber queue instance
        """

        if job_id in self._subscribers:
            self._subscribers[job_id].remove(queue)

            if not self._subscribers[job_id]:
                del self._subscribers[job_id]

event_bus = EventBus()