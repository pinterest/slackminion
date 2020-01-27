import slackminion.slack


class SlackEvent(object):
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
    def text(self):
        if 'text' in self.data:
            return self.data['text']
        elif 'message' in self.data:
            return self.data['message'].get('text', '')

    @property
    def ts(self):
        if 'message' in self.data:
            return self.data['message'].get('ts')
        elif 'ts' in self.data:
            return self.data['ts']

    @property
    def thread_ts(self):
        if 'message' in self.data:
            return self.data['message'].get('thread_ts')
        elif 'thread_ts' in self.data:
            return self.data['ts']

    def __repr__(self):
        return f'SlackEvent type {self.event_type} User: {self.user_id}'
