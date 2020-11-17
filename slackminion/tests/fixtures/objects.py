from .variables import *
from slackminion.plugin import BasePlugin, cmd
from slackminion.utils.util import strip_formatting


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

    @cmd(reply_in_thread=True, reply_broadcast=True)
    async def asyncabc(self, msg, args):
        return 'asyncabc response'

    @cmd(parse=True)
    async def asyncparse(self, msg, args):
        return 'async parse command #parse'

    @cmd(strip_formatting=True)
    async def stripformat(self, msg, args):
        return strip_formatting(' '.join(args))
