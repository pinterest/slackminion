import logging

from user import SlackUser


class SlackRoomAttribute(object):
    def __init__(self):
        self.data = None

    def __get__(self, instance, owner):
        if self.data is None:
            instance._load_extra_attributes()
        return self.data

    def __set__(self, instance, value):
        self.data = value


class SlackRoomTopic(SlackRoomAttribute):
    def __set__(self, instance, value):
        prev_value = self.data
        super(SlackRoomTopic, self).__set__(instance, value)
        if prev_value is not None and prev_value != value:
            instance.set_topic(value)


class SlackRoomIMBase(object):
    def __init__(self, id, sc=None):
        self.id = id
        self._sc = sc
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.setLevel(logging.DEBUG)


class SlackIM(SlackRoomIMBase):
    def __init__(self, id, sc=None):
        super(SlackIM, self).__init__(id, sc)
        self.is_im = True

    @property
    def channel(self):
        self.logger.warn('Use of channel is deprecated, use id instead')
        return self.id

    @property
    def name(self):
        return self.id

    def __str__(self):
        return '<#%s|%s>' % (self.id, self.id)

    def __repr__(self):
        return self.id


class SlackRoom(SlackRoomIMBase):

    BASE_ATTRIBUTES = [
        'created',
        'creator',
        'is_archived',
        'members',
        'name',
        'purpose',
        ('topic', SlackRoomTopic)
    ]

    def __init__(self, id, sc=None):
        super(SlackRoom, self).__init__(id, sc)
        self._name = None

        # Extra information (lazy loaded)
        self._add_extra_attributes()

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

    def _get_extra_attribute(self, name):
        if getattr(self, '_' + name) is None:
            self._load_extra_attributes()
        return getattr(self, '_' + name)

    @staticmethod
    def get_channel(sc, channel_name):
        resp = sc.server.channels.find(channel_name)
        if resp is None:
            return None
        channel_class = SlackChannel
        if resp.id[0] == 'G':
            channel_class = SlackGroup
        channel = channel_class(resp.id, sc)
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
    API_PREFIX = 'channels'
    ATTRIBUTE_KEY = 'channel'
    EXTRA_ATTRIBUTES = [
        'is_channel',
        'is_general',
    ]


class SlackGroup(SlackChannel):
    API_PREFIX = 'groups'
    ATTRIBUTE_KEY = 'group'
    EXTRA_ATTRIBUTES = [
        'is_group',
        'is_mpim',
    ]
