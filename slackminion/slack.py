class SlackEvent(object):
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


class SlackUser(object):
    def __init__(self, userid, sc=None):
        self.userid = userid
        self._sc = sc
        self._username = None

    @property
    def username(self):
        if self._username is None and self._sc is not None:
            resp = self._sc.api_call('users.info', user=self.userid)
            self._username = resp['user']['name']
        return self._username

    @staticmethod
    def get_user(sc, username):
        resp = sc.server.users.find(username)
        if resp is None:
            return None
        user = SlackUser(resp.id, sc)
        return user

    def __str__(self):
        return '<@%s|%s>' % (self.userid, self.username)

    def __repr__(self):
        return self.userid


class SlackChannel(object):
    def __init__(self, channelid, sc=None):
        self.channelid = channelid
        self._sc = sc
        self._channel = None

        # Extra information (lazy loaded)
        self.extra_attributes = [
            'created',
            'creator',
            'is_archived',
            'is_general',
            'is_member',
            'purpose',
            ('topic', SlackChannelTopic)
        ]

        for attribute in self.extra_attributes:
            attribute_class = SlackChannelExtraAttribute
            if isinstance(attribute, tuple):
                attribute, attribute_class = attribute
            setattr(SlackChannel, attribute, attribute_class())

    @property
    def channel(self):
        if self._channel is None and self._sc is not None:
            resp = self._sc.server.channels.find(self.channelid)
            self._channel = resp.name
        return self._channel

    def set_topic(self, topic):
        self._sc.api_call('channels.setTopic', channel=self.channelid, topic=topic)

    def _get_extra_attribute(self, name):
        if getattr(self, '_' + name) is None:
            self._load_extra_attributes()
        return getattr(self, '_' + name)

    def _load_extra_attributes(self):
        resp = self._sc.api_call('channels.info', channel=self.channelid)
        for k, v in resp['channel'].items():
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
        channel = SlackChannel(resp.id, sc)
        return channel

    def __str__(self):
        return '<#%s|%s>' % (self.channelid, self.channel)

    def __repr__(self):
        return self.channelid


class SlackChannelExtraAttribute(object):
    def __init__(self):
        self.data = None

    def __get__(self, instance, owner):
        if self.data is None:
            instance._load_extra_attributes()
        return self.data

    def __set__(self, instance, value):
        self.data = value


class SlackChannelTopic(SlackChannelExtraAttribute):
    def __set__(self, instance, value):
        prev_value = self.data
        super(SlackChannelTopic, self).__set__(instance, value)
        if prev_value is not None and prev_value != value:
            instance.set_topic(value)
