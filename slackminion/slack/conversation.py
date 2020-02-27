import logging


class SlackConversation(object):
    user = None
    conversation = None
    _topic = None

    def __init__(self, conversation, api_client):
        """Base class for rooms (channels, groups) and IMs"""
        self.api_client = api_client
        self.conversation = conversation  # the dict slack sent us
        if conversation:
            self._topic = conversation.get('topic', {}).get('value')
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.setLevel(logging.DEBUG)

    def __getattr__(self, item):
        return self.conversation.get(item)

    @property
    def all_names(self):
        return [self.name, self.conversation.get('normalized_name')] + self.conversation.get('previous_names', [])

    @property
    def channel(self):
        if self.conversation:
            return self.conversation.get('id')

    @property
    def channel_id(self):
        return self.channel

    @property
    def topic(self):
        return self._topic

    @topic.setter
    def topic(self, new_topic):
        self._topic = new_topic
        self.api_client.conversations_setTopic(channel=self.id, topic=new_topic)

    async def load(self, channel_id):
        resp = await self.api_client.conversations_info(channel=channel_id)
        if resp:
            self.conversation = resp['channel']
        else:
            raise RuntimeError('Unable to load channel')

    def _load_extra_attributes(self):
        resp = self.api_client.conversations_info(channel=self.channel_id)
        if resp:
            self.conversation = resp['channel']

    @property
    def formatted_name(self):
        return '<#%s|%s>' % (self.id, self.name)

    def __repr__(self):
        return self.formatted_name

    def get_channel(self):
        return self
