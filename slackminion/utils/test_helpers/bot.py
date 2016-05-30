from slackminion.bot import Bot
from slackminion.webserver import Webserver


class DummyBot(Bot):
    def __init__(self, *args, **kwargs):
        super(DummyBot, self).__init__(None, *args, **kwargs)
        setattr(self, 'start', lambda: None)
        setattr(self, 'send_message', lambda x, y: None)
        self.webserver = Webserver('127.0.0.1', '9999')
