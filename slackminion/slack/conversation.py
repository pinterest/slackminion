import logging


class SlackConversation(object):
    user = None
    conversation = None

    def __init__(self, conversation, api_client):
        """Base class for rooms (channels, groups) and IMs"""
        self.api_client = api_client
        self.conversation = conversation  # the dict slack sent us
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.setLevel(logging.DEBUG)

    def __getattr__(self, item):
        return self.conversation.get(item, False)

    @property
    def channel(self):
        if self.conversation:
            return self.conversation.get('id')

    @property
    def channel_id(self):
        return self.channel

    def set_topic(self, topic):
        self.api_client.conversations_setTopic(channel=self.id, topic=topic)

    async def load(self, channel_id):
        resp = await self.api_client.conversations_info(channel=channel_id)
        if resp:
            self.conversation = resp['channel']
        else:
            raise RuntimeError('Unable to load channel')

    @property
    def formatted_name(self):
        return '<#%s|%s>' % (self.id, self.name)

    def get_channel(self):
        return self
