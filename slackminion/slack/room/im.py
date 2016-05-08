from base import SlackRoomIMBase


class SlackIM(SlackRoomIMBase):
    def __init__(self, id, sc=None):
        super(SlackIM, self).__init__(id, sc)
        self.is_im = True

    @property
    def channel(self):
        self.logger.warn('Use of channel is deprecated, use id instead')
        return self.name

    @property
    def name(self):
        return self.id

    def __str__(self):
        return '<#%s|%s>' % (self.id, self.id)

    def __repr__(self):
        return self.id
