from .room import SlackChannel, SlackGroup, SlackIM
from .user import SlackUser

from six import string_types

class SlackEvent(object):
    """Encapsulates an event received from the RTM socket"""
    def __init__(self, event_type, sc=None, **payload):
        self.event_type = event_type
        self._sc = sc
        self.rtm_client = payload.get('rtm_client')
        self.web_client = payload.get('web_client')
        self._channel = None
        self._user = None
        data = payload.get('data')
        try:
            for k, v in data.items():
                setattr(self, k, v)
        except AttributeError:
            pass

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        if isinstance(value, string_types):
            if value[0] == 'G':
                # Slack groups have an ID starting with 'G'
                self._channel = SlackGroup(value, sc=self.web_client)
            elif value[0] == 'D':
                # Slack IMs have an ID starting with 'D'
                self._channel = SlackIM(value, sc=self.web_client)
            else:
                self._channel = SlackChannel(value, sc=self.web_client)
        else:
            self._channel = value

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        if isinstance(value, string_types):
            self._user = SlackUser(value, sc=self._sc)
        else:
            self._user = value
