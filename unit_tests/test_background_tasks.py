import threading

from robyn.background import BackgroundTask, BackgroundTasks


def test_background_task_sync():
    results = []

    def append_result(value):
        results.append(value)

    task = BackgroundTask(append_result, "hello")
    task()
    assert results == ["hello"]


def test_background_task_async():
    results = []

    async def async_append(value):
        results.append(value)

    task = BackgroundTask(async_append, "async_hello")
    task()
    assert results == ["async_hello"]


def test_background_tasks_collection():
    results = []

    def task_a():
        results.append("a")

    def task_b(x):
        results.append(x)

    tasks = BackgroundTasks()
    tasks.add_task(task_a)
    tasks.add_task(task_b, "b")

    assert len(tasks) == 2
    tasks.run()
    assert results == ["a", "b"]


def test_background_tasks_run_in_thread():
    event = threading.Event()
    results = []

    def slow_task():
        results.append("done")
        event.set()

    tasks = BackgroundTasks()
    tasks.add_task(slow_task)
    tasks.run_in_thread()

    event.wait(timeout=5)
    assert results == ["done"]


def test_background_tasks_error_handling():
    results = []

    def failing_task():
        raise ValueError("fail")

    def ok_task():
        results.append("ok")

    tasks = BackgroundTasks()
    tasks.add_task(failing_task)
    tasks.add_task(ok_task)
    tasks.run()
    assert results == ["ok"]
