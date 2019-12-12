import pytest
import mock

from slackminion.plugin import BasePlugin
import slackminion.plugin.base

from slackminion.tests.fixtures import *


def dummy_func(self):
    self.xyzzy = True


test_mapping = {
    test_channel_name: test_channel_id,
    test_group_name: test_group_id,
    test_user_name: test_user_id,
}
test_user_manager = [
    (test_user_name,)
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

    @mock.patch('slackminion.plugin.base.SlackChannel')
    def test_get_channel(self, mock_channel):
        mock_channel.get_channel.return_value = TestChannel()
        channel = self.object.get_channel(test_channel_name)
        assert channel.id == test_channel_id
        assert channel.name == test_channel_name

    @mock.patch('slackminion.plugin.base.SlackUser')
    def test_get_user_without_user_manager(self, mock_user):
        mock_user.get_user.return_value = TestUser()
        self.object._bot.user_manager = None
        delattr(self.object._bot, 'user_manager')
        user = self.object.get_user(test_user_name)
        assert user.id == test_user_id
        assert user.username == test_user_name

    def test_get_user_user_manager(self):
        self.object._bot.user_manager.get_by_username.return_value = test_user
        test_user._sc.server.users.find.return_value = TestUser()
        user = self.object.get_user(test_user_name)
        self.object._bot.user_manager.get_by_username.assert_called_with(test_user_name)
        assert user.id == test_user_id
        assert user.username == test_user_name

    def test_get_user_fail_nonexistent(self):
        self.object._bot.user_manager.get_by_username.return_value = None
        test_user._sc.server.users.find.return_value = None
        self.object._bot.sc.server.users.find.return_value = None
        user = self.object.get_user(non_existent_user_name)
        self.object._bot.user_manager.get_by_username.assert_called_with(non_existent_user_name)
        assert user is None

    @pytest.mark.parametrize('channel,result', test_message_data)
    def test_send_message(self, channel, result):
        self.object._bot = mock.Mock()
        expected_method = getattr(self.object._bot, result)

        self.object.send_message(channel, 'Yet another test string')
        expected_method.assert_called()

        self.object.send_message(channel, 'Yet another test string', thread=12345.67,
                                 reply_broadcast=True)
        expected_method.assert_called()
