import logging


class SlackUser(object):
    """Represents a Slack user"""
    def __init__(self, id, sc=None):
        self.id = id
        self._sc = sc
        self._username = None
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.setLevel(logging.DEBUG)

    @property
    def username(self):
        if self._username is None and self._sc is not None:
            resp = self._sc.api_call('users.info', user=self.id)
            self._username = resp['user']['name']
        return self._username

    @property
    def userid(self):
        self.logger.warn('Use of userid is deprecated, use id instead')
        return self.id

    @staticmethod
    def get_user(sc, username):
        resp = sc.server.users.find(username)
        if resp is None:
            return None
        user = SlackUser(resp.id, sc)
        return user

    def __str__(self):
        return '<@%s|%s>' % (self.id, self.username)

    def __repr__(self):
        return self.id
