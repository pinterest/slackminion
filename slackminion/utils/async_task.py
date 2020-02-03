from contextlib import suppress
import asyncio
import logging
import time
import functools
import inspect
import multiprocessing

NUM_CPUS = multiprocessing.cpu_count()


class CallLater:
    called = False
    partial_func = None
    timer_handle = None

    def __init__(self, func, delay, loop=None, *args, **kwargs):
        self.log = logging.getLogger(type(self).__name__)
        self.func = func
        self.args = args
        self.delay = delay
        if loop:
            self.event_loop = loop
        else:
            self.event_loop = asyncio.get_event_loop()
        self.kwargs = kwargs
        self.name = f'{self.func.__name__}_{int(time.time())}'

    def schedule(self):
        self.log.debug(f'Scheduling func {self.name}')
        self.partial_func = functools.partial(self.func, *self.args, **self.kwargs)
        self.timer_handle = self.event_loop.call_later(self.delay, self.run_and_update_status)

    def run_and_update_status(self):
        self.partial_func()
        self.called = True

    def cancel(self):
        self.timer_handle.cancel()


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
    delayed_tasks = []
    awaited_tasks = []

    def __init__(self):
        self.log = logging.getLogger(type(self).__name__)
        self.event_loop = asyncio.get_event_loop()

    def schedule_task(self, task):
        self.tasks.append(task)

    async def start(self):
        self.log.debug('Starting task waiter')
        while self.runnable:
            try:
                self.log.debug('tick')
                for task in self.tasks:
                    await asyncio.sleep(1)
                    if task not in self.awaited_tasks:
                        self.log.debug(f'awaiting task: {task}')
                        try:
                            await task
                            if task.done():
                                try:
                                    self.log.debug(f'task {task} ended with result {task.result()}')
                                except asyncio.CancelledError:
                                    self.log.debug(f'task {task} was cancelled')
                                finally:
                                    self.log.debug(f'removing task: {task}')
                                    self.tasks.remove(task)
                        except Exception:
                            self.log.exception(f"Unexpected exception caught awaiting {task}!")
                        finally:
                            self.awaited_tasks.append(task)
                for periodic in self.periodic_tasks:
                    if not periodic.is_started:
                        await periodic.start()
                for delayed in self.delayed_tasks:
                    if delayed.called:
                        self.delayed_tasks.remove(delayed)
            except Exception as e:
                self.log.exception("Unexpected exception caught in task loop!")

    def create_and_schedule_task(self, func, *args, **kwargs):
        self.log.info(f'creating task for {func.__name__}({args}, {kwargs})')
        if isinstance(func, asyncio.Task):
            task = func
        elif inspect.iscoroutinefunction(func):
            task = asyncio.create_task(func(*args, **kwargs))
        else:
            raise RuntimeError('create_and_schedule_task can only be run with async functions or tasks.')
        self.schedule_task(task)
        return task

    async def shutdown(self):
        self.log.debug('AsyncTaskManager: shutting down')
        self.runnable = False
        for task in self.tasks:
            task.cancel()
        for periodic in self.periodic_tasks:
            await periodic.stop()
        for timer in self.delayed_tasks:
            timer.cancel()

    def start_periodic_task(self, period, func, *args, **kwargs):
        task = AsyncTimer(period, func, *args, **kwargs)
        self.periodic_tasks.append(task)

    def start_timer(self, delay, func, *args, **kwargs):
        if inspect.iscoroutinefunction(func):
            raise RuntimeError('Timer can only be run on non-async functions.')
        task = CallLater(func, delay, self.event_loop, *args, **kwargs)
        if task.name not in self.delayed_tasks:
            self.delayed_tasks.append(task)
            task.schedule()
        else:
            self.log.debug(f'start_timer called for {task.name} but it was already scheduled.')

    def stop_timer(self, func_name):
        try:
            timer = self.delayed_tasks.pop(func_name)
            timer.cancel()
        except KeyError:
            self.log.exception(f'stop_timer called with unknown func {func_name}')
