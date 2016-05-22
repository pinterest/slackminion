import pytest

from slackminion.plugins.core.core import Core
from slackminion.utils.test_helpers import *

# command, help
test_help_long_data = [
    ('!sleep', """Causes the bot to ignore all messages from the channel.

        Usage:
        !sleep [channel name] - ignore the specified channel (or current if none specified)
        """),
    ('!abc', 'No description provided.'),
    ('!nosuchcommand', 'No such command: !nosuchcommand')
]

test_help_short_data = [
    ('!sleep', "*!sleep*: Causes the bot to ignore all messages from the channel."),
    ('!abc', '*!abc*: No description provided.'),
]


class TestCorePlugin(BasicPluginTest):
    PLUGIN_CLASS = Core
    ADMIN_COMMANDS = [
        'save',
        'shutdown',
        'wake',
    ]

    def test_help(self):
        assert self.object.help(get_test_event(), []) == ''

    def test_help_for_command(self):
        self.object._bot.dispatcher.register_plugin(self.object)
        assert self.object.help(get_test_event(), ['help']) == 'Displays help for each command'

    def test_save(self):
        e = get_test_event()
        assert self.is_called('slackminion.plugin.PluginManager.save_state', self.object.save, e, [])

    def test_shutdown(self):
        self.object.shutdown(get_test_event(), None)
        assert self.bot.runnable is False

    def test_whoami(self):
        from slackminion.plugins.core import version
        output = self.object.whoami(get_test_event(), None)
        assert output == 'Hello <@U12345678|testuser>\nBot version: %s-HEAD' % version

    def test_sleep(self):
        e = get_test_event()
        assert self.is_called('slackminion.dispatcher.MessageDispatcher.ignore', self.object.sleep, e, [])

    def test_sleep_channel(self):
        e = get_test_event()
        assert self.is_called('slackminion.dispatcher.MessageDispatcher.ignore', self.object.sleep, e, ['testchannel'])

    def test_wake(self):
        e = get_test_event()
        assert self.is_called('slackminion.dispatcher.MessageDispatcher.unignore', self.object.wake, e, [])

    def test_wake_channel(self):
        e = get_test_event()
        assert self.is_called('slackminion.dispatcher.MessageDispatcher.unignore', self.object.wake, e, ['testchannel'])

    @pytest.mark.parametrize('command,helpstr', test_help_long_data)
    def test_get_help_for_command(self, command, helpstr):
        self.object._bot.dispatcher.register_plugin(self.object)
        self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
        assert self.object._get_help_for_command(command) == helpstr

    @pytest.mark.parametrize('command,helpstr', test_help_short_data)
    def test_get_short_help_for_command(self, command, helpstr):
        self.object._bot.dispatcher.register_plugin(self.object)
        self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
        assert self.object._get_short_help_for_command(command) == helpstr
