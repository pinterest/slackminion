import logging


def cmd(func):
    func.is_cmd = True
    return func


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
        self.bot = bot
        self.config = {}
        if 'config' in kwargs:
            self.config = kwargs['config']

    def on_load(self):
        pass

    def on_unload(self):
        pass

    def send_message(self, channel, text):
        self.bot.send_message(channel, text)
