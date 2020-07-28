from slackminion.plugins.core.core import Core
from slackminion.tests.fixtures import *
from slackminion.utils.util import format_docstring
from slackminion.dispatcher import MessageDispatcher
from slackminion.webserver import Webserver
import slackminion.plugin.base

# command, help
test_help_long_data = [
    ('!sleep', format_docstring("""Causes the bot to ignore all messages from the channel.

        Usage: !sleep [channel name] - ignore the specified channel (or current if none specified)
        """)),
    ('!abc', 'No description provided.'),
    ('!nosuchcommand', 'No such command: !nosuchcommand')
]

test_help_short_data = [
    ('!sleep', "*!sleep*: Causes the bot to ignore all messages from the channel."),
    ('!abc', '*!abc*: No description provided.'),
]

test_payload = {
    'rtm_client': mock.Mock(),
    'web_client': mock.Mock(),
    'data': {
        'user': test_user_id,
        'name': test_user_name,
        'channel': test_channel_id,
    },
}


class BasicPluginTest(object):
    PLUGIN_CLASS = None
    BASE_METHODS = ['on_load', 'on_connect', 'on_unload']
    ADMIN_COMMANDS = []

    @mock.patch('slackminion.slack.SlackUser')
    def setUp(self, mock_user):
        mock_user.return_value = test_user
        bot = mock.Mock()
        if self.PLUGIN_CLASS:
            self.object = self.PLUGIN_CLASS(bot)
            self.test_event = SlackEvent(event_type='tests', **test_payload)
            self.test_event.user = mock.Mock()

    def tearDown(self):
        self.object = None

    def test_has_base_method(self):
        if self.object:
            for method in EXPECTED_PLUGIN_METHODS:
                assert hasattr(self.object, method)

    def test_method_returns_true(self):
        if self.object:
            for method in EXPECTED_PLUGIN_METHODS:
                f = getattr(self.object, method)
                assert f() is True

    def test_admin_commands(self):
        for c in self.ADMIN_COMMANDS:
            assert getattr(self.object, c).admin_only is True


class TestCorePlugin(BasicPluginTest, unittest.TestCase):
    PLUGIN_CLASS = Core
    ADMIN_COMMANDS = [
        'save',
        'shutdown',
        'wake',
    ]

    def test_help(self):
        self.object._bot.dispatcher.commands = {}
        self.object._should_filter_help_commands = mock.Mock(return_value=False)
        assert self.object.help(self.test_event, []) == ''

    def test_help_for_command(self):
        self.object._bot.dispatcher = MessageDispatcher()
        self.object._bot.webserver = Webserver(test_host, test_port)
        self.object._bot.dispatcher.register_plugin(self.object)
        assert self.object.help(self.test_event, ['help']) == format_docstring('Displays help for each command')

    def test_save(self):
        self.object.send_message = mock.Mock()
        self.object.save(self.test_event, [])

        assert self.object.send_message.call_count == 2

    def test_shutdown(self):
        self.object.shutdown(self.test_event, None)
        assert self.object._bot.runnable is False

    @async_test
    async def test_whoami(self):
        self.object._bot.api_client.users_info = AsyncMock()
        self.object._bot.api_client.users_info.coro.return_value = test_user_response
        self.object._bot.commit = test_commit
        from slackminion.plugins.core import version
        self.object._bot.version = version
        self.test_event.user = SlackUser(api_client=self.object._bot.api_client, user_id=test_payload.get('data').get('user'))
        await self.test_event.user.load()
        output = self.object.whoami(self.test_event, None)
        assert output == f'Hello <@{test_user_id}|{test_user_name}>\nBot version: {version}-{test_commit}'

    def test_sleep(self):
        self.object._get_channel_from_msg_or_args = mock.Mock(return_value=TestChannel)
        self.object.sleep(self.test_event, [])
        self.object._bot.dispatcher.ignore.assert_called_with(TestChannel)

    def test_sleep_channel(self):
        self.object._get_channel_from_msg_or_args = mock.Mock(return_value=TestChannel)
        self.object.sleep(self.test_event, [test_channel_name])
        self.object._bot.dispatcher.ignore.assert_called_with(TestChannel)

    def test_wake(self):
        self.object._get_channel_from_msg_or_args = mock.Mock(return_value=TestChannel)
        self.object.wake(self.test_event, [])
        self.object._bot.dispatcher.unignore.assert_called_with(TestChannel)

    @mock.patch('slackminion.plugin.base.SlackConversation')
    def test_wake_channel(self, mock_slackchannel):
        mock_slackchannel.return_value = test_conversation
        self.object.send_message = mock.Mock()
        self.object.wake(test_conversation, [test_channel_name])
        self.object.send_message.assert_called()

    def test_get_help_for_command(self):
        for command, helpstr in test_help_long_data:
            self.object._bot.dispatcher = MessageDispatcher()
            self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
            assert self.object._get_help_for_command(command) == helpstr

    def test_get_short_help_for_command(self):
        for command, helpstr in test_help_short_data:
            self.object._bot.dispatcher = MessageDispatcher()
            self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
            assert self.object._get_short_help_for_command(command) == helpstr


if __name__ == "__main__":
    unittest.main()
