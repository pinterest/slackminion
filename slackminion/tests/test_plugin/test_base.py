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


class TestBasePlugin(unittest.TestCase):
    def setUp(self):
        dummy_bot = mock.Mock()
        self.plugin = BasePlugin(dummy_bot)

    def tearDown(self):
        self.plugin = None

    def test_on_load(self):
        assert hasattr(self.plugin, 'on_load')
        assert self.plugin.on_load() is True

    def test_on_unload(self):
        assert hasattr(self.plugin, 'on_unload')
        assert self.plugin.on_unload() is True

    def test_on_connect(self):
        assert hasattr(self.plugin, 'on_connect')
        assert self.plugin.on_connect() is True

    def test_start_timer(self):
        self.plugin.start_timer(30, dummy_func, self.plugin)
        assert dummy_func in self.plugin._timer_callbacks

    def test_stop_timer(self):
        self.plugin.start_timer(30, dummy_func, self.plugin)
        assert dummy_func in self.plugin._timer_callbacks
        self.plugin.stop_timer(dummy_func)
        assert dummy_func not in self.plugin._timer_callbacks

    def test_get_channel(self):
        self.plugin.get_channel(test_channel_name)
        self.plugin._bot.get_channel.assert_called()

    @mock.patch('slackminion.plugin.base.SlackUser')
    def test_get_user_without_user_manager(self, mock_user):
        mock_user.load_user_from_slack.return_value = TestUser()
        self.plugin._bot.user_manager = None
        delattr(self.plugin._bot, 'user_manager')
        user = self.plugin.get_user(test_user_name)
        assert user.id == test_user_id
        assert user.username == test_user_name

    def test_get_user_from_user_manager(self):
        self.plugin._bot.user_manager.get_by_username.return_value = test_user
        user = self.plugin.get_user(test_user_name)
        self.plugin._bot.user_manager.get_by_username.assert_called_with(test_user_name)
        assert user.id == test_user_id
        assert user.username == test_user_name

    def test_get_user_fail_nonexistent(self):
        self.plugin._bot.user_manager.get_by_username.return_value = None
        test_user.api_client.users_info.find.return_value = None
        self.plugin._bot.sc.server.users.find.return_value = None
        user = self.plugin.get_user(non_existent_user_name)
        self.plugin._bot.user_manager.get_by_username.assert_called_with(non_existent_user_name)
        assert user is None

    def test_send_message(self):
        self.plugin._bot = mock.Mock()
        self.plugin.send_message(test_channel, 'Yet another test string')
        self.plugin._bot.send_message.assert_called()

