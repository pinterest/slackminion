class SlackEvent(object):
    _channel = None
    """Encapsulates an event received from the RTM socket"""

    def __init__(self, event_type, **payload):
        self.event_type = event_type
        self.rtm_client = payload.get('rtm_client')
        self.web_client = payload.get('web_client')
        self.data = payload.get('data')
        self.subtype = payload.get('subtype')
        self.user_id = self.data.get('user')
        self.channel_id = self.data.get('channel')

    @property
    def channel(self):
        if self._channel:
            return self._channel
        return self.channel_id

    @channel.setter
    def channel(self, c):
        self._channel = c

    @property
    def text(self):
        if 'text' in self.data:
            return self.data['text']
        elif 'message' in self.data:
            return self.data['message'].get('text', '')
        return ''

    @property
    def ts(self):
        return self.data.get('ts', self.data.get('event_ts'))

    @property
    def thread_ts(self):
        return self.data.get('thread_ts')

    @property
    def event_ts(self):
        return self.data.get('event_ts')

    def __repr__(self):
        return f'SlackEvent type {self.event_type} User: {self.user_id}'
