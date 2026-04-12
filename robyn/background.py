import asyncio
import inspect
import logging
import threading
from typing import Any, Callable, List

_logger = logging.getLogger(__name__)


class BackgroundTask:
    """A single background task to be executed after the response is sent."""

    def __init__(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.is_async = inspect.iscoroutinefunction(func) or (
            callable(func)
            and inspect.iscoroutinefunction(getattr(func, "__call__", None))
        )

    def __call__(self) -> None:
        if self.is_async:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self.func(*self.args, **self.kwargs))
            finally:
                loop.close()
        else:
            self.func(*self.args, **self.kwargs)


class BackgroundTasks:
    """Collection of tasks to run after the response is sent.

    Usage::

        @app.post("/send-email")
        async def send_email(request):
            tasks = BackgroundTasks()
            tasks.add_task(send_welcome_email, user_email="user@example.com")
            tasks.add_task(log_signup, user_id=42)
            return {"status": "accepted"}, tasks
    """

    def __init__(self) -> None:
        self._tasks: List[BackgroundTask] = []

    def add_task(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """Add a task to be run in the background after the response is sent."""
        self._tasks.append(BackgroundTask(func, *args, **kwargs))

    def run(self) -> None:
        """Execute all tasks. Called by the framework after the response is sent."""
        for task in self._tasks:
            try:
                task()
            except Exception:
                func_name = getattr(task.func, "__name__", None) or getattr(
                    task.func, "__qualname__", repr(task.func)
                )
                _logger.exception("Background task %s failed", func_name)

    def run_in_thread(self) -> None:
        """Execute all tasks in a background thread."""
        if not self._tasks:
            return
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()

    def __len__(self) -> int:
        return len(self._tasks)
