from .variables import *
from slackminion.bot import Bot

from slackminion.webserver import Webserver
from slackminion.plugin import BasePlugin, cmd


class TestChannel(object):
    id = test_channel_id
    name = test_channel_name


class DummyServer(object):
    def __init__(self):
        self.channels = mock.Mock()
        self.users = mock.Mock()


class DummySlackConnection(object):
    def __init__(self):
        self.server = DummyServer()
        self.topic = 'Test Topic'

    def api_call(self, name, *args, **kwargs):
        if 'setTopic' in name:
            self.topic = kwargs['topic']
        api_responses = {
            'channels.info': {
                'channel': {
                    'name': test_channel_name,
                    'creator': test_user_id,
                    'topic': {
                        'value': self.topic,
                    },
                },
            },
            'channels.setTopic': {
                'topic': self.topic,
            },
            'groups.info': {
                'group': {
                    'name': test_group_name,
                    'creator': test_user_id,
                    'topic': {
                        'value': self.topic,
                    },
                },
            },
            'groups.setTopic': {
                'topic': self.topic,
            },
            'users.info': {
                'user': {
                    'id': test_user_id,
                    'name': test_user_name,
                },
            }
        }
        return api_responses[name]


class DummyBot(Bot):
    def __init__(self, *args, **kwargs):
        super(DummyBot, self).__init__(None, *args, **kwargs)
        setattr(self, 'start', lambda: None)
        setattr(self, 'send_message', lambda x, y, z, a: None)
        self.webserver = Webserver('127.0.0.1', '9999')


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


class TestUser(object):
    name = test_user_name
    id = test_user_id
    username = test_user_name
