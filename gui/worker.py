"""
Background worker thread for running UniversalTester workloads without freezing the GUI.
"""
import threading
from typing import Callable, Optional
from core.models import RunRequest, RunResult
from core.events import ProgressEvent
from core.service import TesterService


class AsyncTestRunner:
    """Manages asynchronous test execution in a dedicated background worker thread."""

    def __init__(self, service: TesterService):
        self.service = service
        self._thread: Optional[threading.Thread] = None
        self._current_run_id: Optional[str] = None

    def is_running(self) -> bool:
        """Check if a test workload is currently executing."""
        return self._thread is not None and self._thread.is_alive()

    def start_run(
        self,
        request: RunRequest,
        on_event: Callable[[ProgressEvent], None],
        on_complete: Callable[[RunResult], None]
    ) -> None:
        """Execute a test run asynchronously in a background thread."""
        if self.is_running():
            return

        def _worker():
            def _event_wrapper(evt: ProgressEvent):
                self._current_run_id = evt.run_id
                on_event(evt)

            result = self.service.run(request, on_event=_event_wrapper)
            self._current_run_id = None
            on_complete(result)

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        """Cancel active execution if running."""
        if self._current_run_id:
            self.service.cancel(self._current_run_id)
