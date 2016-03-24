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

    def __str__(self):
        return '<@%s|%s>' % (self.userid, self.username)

    def __repr__(self):
        return self.userid


class SlackChannel(object):
    def __init__(self, channelid, sc=None):
        self.channelid = channelid
        self._sc = sc
        self._channel = None

    @property
    def channel(self):
        if self._channel is None and self._sc is not None:
            resp = self._sc.server.channels.find(self.channelid)
            self._channel = resp.name
        return self._channel

    def __str__(self):
        return '<#%s|%s>' % (self.channelid, self.channel)

    def __repr__(self):
        return self.channelid
