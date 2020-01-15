import asyncio
import logging


class AsyncTaskManager(object):
    tasks = []
    periodic_tasks = []
    sleep_tasks = []

    def __init__(self):
        self.log = logging.getLogger(type(self).__name__)
        self.event_loop = asyncio.get_event_loop()
        self.event_loop = asyncio.get_event_loop()
        self.event_loop.create_task(self._await_tasks())

    def schedule_task(self, task):
        self.tasks.append(task)

    async def _await_tasks(self):
        while True:
            for task in self.tasks:
                self.log.debug(f'awaiting task: {task}')
                await task
                if task.done():
                    self.log.debug(f'removing task: {task}')
                    self.log.debug(f'task {task} ended with result {task.result()}')
                    self.tasks.remove(task)
            for task in self.sleep_tasks:
                self.log.debug(f'awaiting task: {task}')
                if task.done():
                    self.log.debug(f'removing task: {task}')
                    self.log.debug(f'task {task} ended with result {task.result()}')
                    self.tasks.remove(task)
            await asyncio.sleep(0.1)

    def create_and_schedule_task(self, func, *args, **kwargs):
        task = asyncio.create_task(func(*args, **kwargs))
        self.schedule_task(task)
        return task

    def shutdown(self):
        for task in self.tasks:
            task.cancel()
        for task in self.periodic_tasks:
            task.cancel()
        for task in self.sleep_tasks:
            task.cancel()
        pending = asyncio.all_tasks()
        for task in pending:
            task.cancel()

    def add_signal_handler(self, sig, func):
        self.event_loop.add_signal_handler(sig, func)

    async def sleep(self, delay):
        sleep_task = asyncio.create_task(asyncio.sleep(delay))
        self.sleep_tasks.append(sleep_task)
        return sleep_task
