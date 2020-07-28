import logging
import asyncio


class SlackUser(object):
    """Represents a Slack user.
    :param user_id: str
    :param user_info: dict
    :param api_client: slack.WebClient

    Accepts either a user id or 'user' dict from slack response from users.info
    """
    _is_bot_admin = False
    user_info = {}

    def __init__(self, user_id=None, user_info=None, api_client=None):
        self.api_client = api_client
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.setLevel(logging.DEBUG)
        if user_info:
            self.logger.debug(f'Loading user from supplied user_info: {user_info}')
            self.user_info = user_info
            self._user_id = self.user_info.get('id')
        elif user_id:
            self._user_id = user_id
        else:
            raise RuntimeError('Missing user_id or user_info')

    async def load(self):
        if self.user_info:
            return
        self.logger.debug(f'Loading user: {self._user_id}')
        if self.api_client:
            resp = await self.api_client.users_info(user=self._user_id)
            if resp:
                self.user_info = resp.get('user')
            else:
                raise RuntimeError('Failed to load user.')
        else:
            raise RuntimeError('Slack API connectivity not initialized.')

    @property
    def username(self):
        return self.user_info.get('name')

    @property
    def user_id(self):
        return self._user_id

    @property
    def userid(self):
        return self._user_id

    @property
    def id(self):
        return self._user_id

    @property
    def formatted_name(self):
        return '<@%s|%s>' % (self.id, self.username)

    @property
    def at_user(self):
        return self.formatted_name

    @property
    def is_admin(self):
        return self._is_bot_admin

    @property
    def is_bot_admin(self):
        return self._is_bot_admin

    def set_admin(self, value):
        self._is_bot_admin = value

    def __repr__(self):
        return self.formatted_name
