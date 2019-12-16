from .variables import *
from slackminion.plugin import BasePlugin, cmd


class TestChannel(object):
    id = test_channel_id
    name = test_channel_name


class TestUser(object):
    name = test_user_name
    id = test_user_id
    username = test_user_name


class DummyPlugin(BasePlugin):
    @cmd()
    def sleep(self, msg, args):
        """Causes the bot to ignore all messages from the channel.

        Usage: !sleep [channel name] - ignore the specified channel (or current if none specified)
        """

    @cmd(aliases='bca')
    def abc(self, msg, args):
        return 'abcba'

    @cmd(aliases='gfe', reply_in_thread=True)
    def efg(self, msg, args):
        """The efg command."""
        return 'efgfe'

    @cmd(aliases='jih', reply_in_thread=True, reply_broadcast=True)
    def hij(self, msg, args):
        return 'hijih'
