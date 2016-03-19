import logging


def cmd(func):
    func.is_cmd = True
    return func


class BasePlugin(object):
    def __init__(self, bot):
        self.log = logging.getLogger(__name__)
        self.bot = bot

    def on_load(self):
        pass

    def on_unload(self):
        pass

    def send_message(self, channel, text):
        self.bot.send_message(channel, text)
