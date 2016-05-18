from .attributes import SlackRoomAttribute, SlackRoomTopic
from .base import SlackRoomIMBase
from ..user import SlackUser


class SlackRoom(SlackRoomIMBase):
    """Base class for channels and groups.  Provides handling for loading/setting extra attributes"""
    BASE_ATTRIBUTES = [
        'created',
        'creator',
        'is_archived',
        'members',
        'name',
        'purpose',
        ('topic', SlackRoomTopic)
    ]

    def __init__(self, *args, **kwargs):
        super(SlackRoom, self).__init__(*args, **kwargs)

        # Extra information (lazy loaded)
        self._add_extra_attributes()

        for k, v in kwargs.items():
            if k in self.BASE_ATTRIBUTES + self.EXTRA_ATTRIBUTES:
                setattr(self, k, v)

    def set_topic(self, topic):
        self._sc.api_call(self.API_PREFIX + '.setTopic', channel=self.id, topic=topic)

    def _add_extra_attributes(self):
        for attribute in self.BASE_ATTRIBUTES + self.EXTRA_ATTRIBUTES:
            attribute_class = SlackRoomAttribute
            if isinstance(attribute, tuple):
                attribute, attribute_class = attribute
            setattr(SlackChannel, attribute, attribute_class())

    def _load_extra_attributes(self):
        resp = self._sc.api_call(self.API_PREFIX + '.info', channel=self.id)
        for k, v in resp[self.ATTRIBUTE_KEY].items():
            if k == 'creator':
                v = SlackUser(v, sc=self._sc)
            elif k == 'topic':
                v = v['value']
            setattr(self, k, v)

    @staticmethod
    def get_channel(sc, channel_name):
        resp = sc.server.channels.find(channel_name)
        if resp is None:
            return None
        channel_class = SlackChannel
        if resp.id[0] == 'G':
            channel_class = SlackGroup
        channel = channel_class(resp.id, name=resp.name, sc=sc)
        return channel

    @property
    def channel(self):
        self.logger.warn('Use of channel is deprecated, use name instead')
        return self.name

    @property
    def channelid(self):
        self.logger.warn('Use of channelid is deprecated, use id instead')
        return self.id

    def __str__(self):
        return '<#%s|%s>' % (self.id, self.name)

    def __repr__(self):
        return self.id


class SlackChannel(SlackRoom):
    """Represents a Slack channel"""
    API_PREFIX = 'channels'
    ATTRIBUTE_KEY = 'channel'
    EXTRA_ATTRIBUTES = [
        'is_channel',
        'is_general',
    ]


class SlackGroup(SlackChannel):
    """Represents a Slack group (private channel)"""
    API_PREFIX = 'groups'
    ATTRIBUTE_KEY = 'group'
    EXTRA_ATTRIBUTES = [
        'is_group',
        'is_mpim',
    ]
