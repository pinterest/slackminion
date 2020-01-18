import asyncio
import logging
from contextlib import suppress


class AsyncTimer(object):
    def __init__(self, period, func, *args, **kwargs):
        self.log = logging.getLogger(type(self).__name__)
        self.log.debug(f'Scheduling {func.__name__} to run every {period} seconds.')
        self.func = func
        self.period = period
        self.func_args = args
        self.func_kwargs = kwargs
        self.is_started = False
        self._task = None

    async def start(self):
        if not self.is_started:
            self.is_started = True
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        if self.is_started:
            self.is_started = False
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run(self):
        while True:
            await self.func(*self.func_args, **self.func_kwargs)
            await asyncio.sleep(self.period)


class AsyncTaskManager(object):
    runnable = True
    tasks = []
    periodic_tasks = []
    awaited_tasks = []

    def __init__(self):
        self.log = logging.getLogger(type(self).__name__)
        self.event_loop = asyncio.get_event_loop()

    def schedule_task(self, task):
        self.tasks.append(task)

    async def start(self):
        self.log.debug('Starting task waiter')
        while self.runnable:
            self.log.debug('tick')
            for task in self.tasks:
                if task not in self.awaited_tasks:
                    self.log.debug(f'awaiting task: {task}')
                    await task
                    self.awaited_tasks.append(task)
                if task.done():
                    self.log.debug(f'removing task: {task}')
                    self.log.debug(f'task {task} ended with result {task.result()}')
                    self.tasks.remove(task)
            for periodic in self.periodic_tasks:
                if not periodic.is_started:
                    await periodic.start()
            await asyncio.sleep(1)

    def create_and_schedule_task(self, func, *args, **kwargs):
        task = asyncio.create_task(func(*args, **kwargs))
        self.schedule_task(task)
        return task

    async def shutdown(self):
        self.log.debug('AsyncTaskManager: shutting down')
        self.runnable = False
        for task in self.tasks:
            task.cancel()
        for periodic in self.periodic_tasks:
            await periodic.stop()

    async def start_periodic_task(self, period, func, *args, **kwargs):
        task = AsyncTimer(period, func, *args, **kwargs)
        self.periodic_tasks.append(task)
