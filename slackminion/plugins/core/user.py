from slackminion.slack import SlackUser
from slackminion.plugin.base import BasePlugin


class UserManager(BasePlugin):
    """
    Loads and stores user information
    """
    def on_load(self):

        self.users = {}
        self.admins = {}
        if 'bot_admins' in self._bot.config:
            self.admins = self._bot.config['bot_admins']
        setattr(self._bot, 'user_manager', self)

        super(UserManager, self).on_load()

    def get(self, userid):
        if userid in self.users:
            return self.users[userid]
        return None

    def get_by_username(self, username):
        res = filter(lambda x: x.username == username, self.users.values())
        if len(res) > 0:
            return res[0]
        return None

    def set(self, user):
        """
        Adds a user object to the user manager

        user - a SlackUser object
        """

        self.log.info("Loading user rights for %s/%s", user.userid, user.username)
        self.load_user_rights(user)
        self.log.info("Added user: %s/%s", user.userid, user.username)
        self.users[user.userid] = user
        return user

    def load_user_rights(self, user):
        if user.username in self.admins:
            user.is_admin = True
