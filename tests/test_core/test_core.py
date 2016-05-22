from slackminion.plugins.core.core import Core
from slackminion.utils.test_helpers import *


class TestCorePlugin(BasicPluginTest):
    PLUGIN_CLASS = Core
    ADMIN_COMMANDS = [
        'save',
        'shutdown',
        'wake',
    ]

    def test_help(self):
        assert self.object.help(get_test_event(), []) == ''

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
