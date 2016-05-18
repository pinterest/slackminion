from .room import SlackChannel, SlackGroup, SlackIM
from .user import SlackUser


class SlackEvent(object):
    """Encapsulates an event received from the RTM socket"""
    def __init__(self, sc=None, **kwargs):

        self._sc = sc
        self._channel = None
        self._user = None

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        if isinstance(value, basestring):
            if value[0] == 'G':
                # Slack groups have an ID starting with 'G'
                self._channel = SlackGroup(value, sc=self._sc)
            elif value[0] == 'D':
                # Slack IMs have an ID starting with 'D'
                self._channel = SlackIM(value, sc=self._sc)
            else:
                self._channel = SlackChannel(value, sc=self._sc)
        else:
            self._channel = value

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        if isinstance(value, basestring):
            self._user = SlackUser(value, sc=self._sc)
        else:
            self._user = value
