from slackminion.slack import SlackIM, SlackChannel, SlackGroup, SlackUser, SlackEvent
from slackminion.bot import Bot
from slackminion.webserver import Webserver

from unittest import mock
from slackminion.plugin import BasePlugin, cmd
import pytest

test_channel_id = 'C12345678'
test_channel_name = 'testchannel'
test_group_id = 'G12345678'
test_group_name = 'testgroup'
test_user_id = 'U12345678'
test_user_name = 'testuser'
test_user_email = 'root@dev.null'
str_format = '<#{id}|{name}>'
non_existent_user_name = 'doesnotexist'

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
    @cmd(aliases='bca')
    def abc(self, msg, args):
        return 'abcba'

    @cmd(aliases='gfe', reply_in_thread=True)
    def efg(self, msg, args):
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


def get_test_event():
    return SlackEvent(sc=DummySlackConnection(), user=test_user_id, channel=test_channel_id)


class BasicPluginTest(object):
    PLUGIN_CLASS = None
    BASE_METHODS = ['on_load', 'on_connect', 'on_unload']
    ADMIN_COMMANDS = []

    def setup(self):
        self.bot = mock.Mock()
        self.object = self.PLUGIN_CLASS(self.bot)
        self.called = {}

    def teardown(self):
        self.object = None

    def is_called(self, method, test_func, *args, **kwargs):
        from _pytest.monkeypatch import MonkeyPatch

        def called_func(*args, **kwargs):
            self.called[method] = True

        self.called[method] = False
        m = MonkeyPatch()
        m.setattr(method, called_func)
        test_func(*args, **kwargs)
        return self.called[method]

    @pytest.mark.parametrize('method', EXPECTED_PLUGIN_METHODS)
    def test_has_base_method(self, method):
        assert hasattr(self.object, method)

    @pytest.mark.parametrize('method', EXPECTED_PLUGIN_METHODS)
    def test_method_returns_true(self, method):
        f = getattr(self.object, method)
        assert f() is True

    def test_admin_commands(self):
        for c in self.ADMIN_COMMANDS:
            assert getattr(self.object, c).admin_only is True
