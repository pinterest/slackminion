import slackminion.slack


class SlackEvent(object):
    """Encapsulates an event received from the RTM socket"""

    def __init__(self, event_type, **payload):
        self.event_type = event_type
        self.rtm_client = payload.get('rtm_client')
        self.web_client = payload.get('web_client')
        self.data = payload.get('data')
        self.user_id = self.data.get('id')
        if self.user_id:
            self.user = slackminion.slack.SlackUser(user_id=self.user_id, api_client=self.web_client)
        self.channel_id = self.data.get('channel')
        self.channel = slackminion.slack.SlackConversation(self.data, api_client=self.rtm_client)

    def __getattr__(self, item):
        return self.data.get(item)

    def __repr__(self):
        return f'SlackEvent type {self.event_type} User: {self.user}'
