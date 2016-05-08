import logging


class SlackRoomIMBase(object):
    def __init__(self, id, sc=None, **kwargs):
        self.id = id
        self._sc = sc
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.setLevel(logging.DEBUG)
