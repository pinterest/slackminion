from contextlib import suppress
import asyncio
import logging
import time
import functools
import inspect
import signal


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
    shutting_down = False
    rtm_client = None
    rtm_client_task = None

    def __init__(self, bot):
        self._bot = bot
        self.log = logging.getLogger(type(self).__name__)
        self.event_loop = asyncio.get_event_loop()

    def start_rtm_client(self, rtm_client=None):
        if self.runnable:
            if rtm_client:
                self.rtm_client = rtm_client
            self.rtm_client_task = self.rtm_client.start()
            self.add_signal_handlers()

    def add_signal_handlers(self):
        signals = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]
        # these need to be added every time RTMClient starts/restarts, as
        # slackclient adds its own signal handler which overrides these
        for sig in signals:
            if self.event_loop._signal_handlers[sig]._callback != self.graceful_shutdown:
                self.log.debug(f'Adding signal handler for {sig}')
                self.event_loop.add_signal_handler(sig, self.graceful_shutdown)

    async def check_rtm_client(self):
        self.log.debug('Enter check_rtm_client')
        if self.rtm_client_task.done():
            try:
                result = self.rtm_client_task.result()
                self.log.info(f'RTM client task ended with result {result}')
            except asyncio.CancelledError:
                self.log.info('RTM client task was cancelled.')
            except asyncio.TimeoutError:
                self.log.info('RTM client task timed out.')
            except Exception as e:
                self.log.exception(f'Caught unexpected exception: {e}')
            finally:
                if self.runnable:
                    self.log.info('Restarting RTM client')
                    self.start_rtm_client()
                else:
                    self.log.info('Stopping RTM client')
                    self.rtm_client.stop()
                    try:
                        self.rtm_client_task.cancel()
                        await self.rtm_client_task
                    except asyncio.CancelledError:
                        self.log.info("RTM client task cancelled")

    def schedule_task(self, task):
        self.tasks.append(task)

    async def await_tasks(self):
        self.add_signal_handlers()
        if self.runnable:
            await asyncio.sleep(1)
            await self.check_rtm_client()
            pending_tasks = [task for task in self.tasks if task not in self.awaited_tasks]
            self.log.debug(f'tick: Gathering {len(pending_tasks)} tasks...')
            try:
                await asyncio.gather(*pending_tasks)
                for task in pending_tasks:
                    try:
                        if task.done():
                            try:
                                self.log.debug(f'task {task} ended with result {task.result()}')
                            except asyncio.CancelledError:
                                self.log.debug(f'task {task} was cancelled')
                            finally:
                                self.log.debug(f'removing task: {task}')
                                self.tasks.remove(task)
                                self.awaited_tasks.remove(task)
                    except Exception:  # noqa
                        self.log.exception(f"Unexpected exception caught awaiting {task}!")
                    finally:
                        self.awaited_tasks.append(task)
            except Exception:  # noqa
                self.log.exception("Unexpected exception caught during asyncio.gather()")

    async def start(self):
        self.log.debug('Starting task waiter')
        while self.runnable:
            try:
                await self.await_tasks()
                for periodic in self.periodic_tasks:
                    if not periodic.is_started:
                        await periodic.start()
                for delayed in self.delayed_tasks:
                    if delayed.called:
                        self.delayed_tasks.remove(delayed)
            except Exception as e:
                self.log.exception("Unexpected exception caught in task loop!")
        await self.shutdown()

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

    def graceful_shutdown(self):
        if not self.shutting_down:
            self.log.debug('AsyncTaskManager: shutting down')
            self.shutting_down = True
            self.runnable = False
            self._bot.runnable = False

    async def shutdown(self):
        self.rtm_client.stop()
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
