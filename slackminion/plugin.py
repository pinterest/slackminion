import logging
import threading


def cmd(admin_only=False, acl='*', aliases=None, *args, **kwargs):
    def wrapper(func):
        func.is_cmd = True
        func.admin_only = admin_only
        func.acl = acl
        func.aliases = aliases
        return func
    return wrapper


def webhook(*args, **kwargs):
    def wrapper(func):
        func.is_webhook = True
        func.route = args[0]
        func.form_params = kwargs['form_params']
        return func
    return wrapper


class BasePlugin(object):
    def __init__(self, bot, **kwargs):
        self.log = logging.getLogger(__name__)
        self._bot = bot
        self._timer_callbacks = {}
        self.config = {}
        if 'config' in kwargs:
            self.config = kwargs['config']

    def on_load(self):
        pass

    def on_unload(self):
        pass

    def send_message(self, channel, text):
        self._bot.send_message(channel, text)

    def start_timer(self, func, duration):
        t = threading.Timer(duration, self._timer_callback, (func,))
        self._timer_callbacks[func] = t
        t.start()

    def stop_timer(self, func):
        if func in self._timer_callbacks:
            t = self._timer_callbacks[func]
            t.cancel()
            del self._timer_callbacks[func]

    def _timer_callback(self, func):
        del self._timer_callbacks[func]
        func()
