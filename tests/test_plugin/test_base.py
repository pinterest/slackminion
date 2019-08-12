import pytest
import mock

from slackminion.bot import Bot
from slackminion.plugin import BasePlugin
import slackminion.plugin.base
from slackminion.slack import SlackIM, SlackChannel, SlackGroup, SlackUser
from slackminion.utils.test_helpers.slack import test_channel_id, test_channel_name, test_group_id, test_group_name, \
    test_user_id, test_user_name, DummySlackConnection


def dummy_func(self):
    self.xyzzy = True


str_format = '<#{id}|{name}>'

test_mapping = {
    test_channel_name: test_channel_id,
    test_group_name: test_group_id,
    test_user_name: test_user_id,
}

# Channel, result
test_message_data = [
    (SlackIM('D12345678'), 'send_im'),
    (SlackUser(test_user_id), 'send_im'),
    (SlackChannel(test_channel_id), 'send_message'),
    (SlackGroup(test_group_id), 'send_message'),
    ('@testuser', 'send_im'),
    ('#testchannel', 'send_message'),
    ('testchannel', 'send_message'),
    (None, 'send_message'),
]

slackminion.plugin.base.threading = mock.Mock()


class TestBasePlugin(object):
    def setup(self):
        dummy_bot = mock.Mock()
        self.object = BasePlugin(dummy_bot)

    def teardown(self):
        self.object = None

    def test_on_load(self):
        assert hasattr(self.object, 'on_load')
        assert self.object.on_load() is True

    def test_on_unload(self):
        assert hasattr(self.object, 'on_unload')
        assert self.object.on_unload() is True

    def test_on_connect(self):
        assert hasattr(self.object, 'on_connect')
        assert self.object.on_connect() is True

    def test_start_timer(self):
        self.object.start_timer(30, dummy_func, self.object)
        assert dummy_func in self.object._timer_callbacks

    def test_stop_timer(self):
        self.object.start_timer(30, dummy_func, self.object)
        assert dummy_func in self.object._timer_callbacks
        self.object.stop_timer(dummy_func)
        assert dummy_func not in self.object._timer_callbacks

    def test_get_channel(self):
        self.object._bot = Bot(None)
        self.object._bot.sc = DummySlackConnection()
        channel = self.object.get_channel(test_channel_name)
        assert channel.id == test_channel_id
        assert channel.name == test_channel_name

    def test_get_user(self):
        self.object._bot = Bot(None)
        self.object._bot.sc = DummySlackConnection()
        user = self.object.get_user(test_user_name)
        assert user.id == test_user_id
        assert user.username == test_user_name

    def test_get_user_user_manager(self):
        class UserManager(object):
            def get_by_username(self, username):
                if username in test_mapping:
                    u = SlackUser(test_mapping[username])
                    u._username = username
                    return u
                return None

            def set(self, user):
                pass

        class Bot(object):
            def __init__(self):
                self.user_manager = UserManager()

        self.object._bot = Bot()
        self.object._bot.sc = DummySlackConnection()
        user = self.object.get_user(test_user_name)
        assert user.id == test_user_id
        assert user.username == test_user_name

        user = self.object.get_user('doesnotexist')
        assert user is None

    @pytest.mark.parametrize('channel,result', test_message_data)
    def test_send_message(self, channel, result):
        class Bot(object):
            def __init__(self):
                self.method = ''

            def send_im(self, channel, text, thread=None, reply_broadcast=False):
                self.method = 'send_im'

            def send_message(self, channel, text, thread=None, reply_broadcast=False):
                self.method = 'send_message'

        self.object._bot = Bot()
        self.object.send_message(channel, 'Yet another test string')
        assert self.object._bot.method == result
        self.object.send_message(channel, 'Yet another test string', thread=12345.67,
                                 reply_broadcast=True)
        assert self.object._bot.method == result
