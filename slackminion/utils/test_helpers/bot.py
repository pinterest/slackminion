from slackminion.bot import Bot


class DummyBot(Bot):
    def __init__(self, *args, **kwargs):
        super(DummyBot, self).__init__(None, *args, **kwargs)
        setattr(self, 'start', lambda: None)
        setattr(self, 'send_message', lambda x, y: None)
