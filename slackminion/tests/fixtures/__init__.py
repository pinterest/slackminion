from slackminion.slack import SlackIM, SlackChannel, SlackGroup, SlackUser, SlackEvent
from slackminion.bot import Bot
from slackminion.webserver import Webserver
from slackminion.dispatcher import MessageDispatcher

from unittest import mock
from slackminion.plugin import BasePlugin, cmd
import unittest

test_channel_id = 'C12345678'
test_channel_name = 'testchannel'
test_group_id = 'G12345678'
test_group_name = 'testgroup'
test_user_id = 'U12345678'
test_user_name = 'testuser'
test_user_email = 'root@dev.null'
str_format = '<#{id}|{name}>'
non_existent_user_name = 'doesnotexist'
test_version = '0.0.42'
test_commit = '969d561d'
test_host = 'localhost'
test_port = 80
test_text = "Testing 1..2..3.."
test_user = SlackUser(test_user_id, sc=mock.Mock())
# Channel, result
test_message_data = [
    (SlackIM('D12345678'), 'send_im'),
    (SlackUser(test_user_id, sc=mock.Mock()), 'send_im'),
    (SlackChannel(test_channel_id, sc=mock.Mock()), 'send_message'),
    (SlackGroup(test_group_id, sc=mock.Mock()), 'send_message'),
    ('@testuser', 'send_im'),
    ('#testchannel', 'send_message'),
    ('testchannel', 'send_message'),
    (None, 'send_message'),
]

EXPECTED_PLUGIN_METHODS = [
    'on_connect',
    'on_load',
    'on_unload',
]


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





