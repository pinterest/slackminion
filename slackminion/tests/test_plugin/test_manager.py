from slackminion.tests.fixtures import *
from slackminion.plugin import PluginManager


class PluginWithEvents(BasePlugin):
    notify_event_types = [test_event_type]

    def handle_event(self):
        pass


class TestPluginManager(unittest.TestCase):

    def setUp(self):
        self.bot = mock.Mock()
        self.object = PluginManager(self.bot)

    def test_on_unload(self):
        fake_plugin = mock.Mock()
        self.object.plugins = [fake_plugin]
        self.object.unload_all()
        fake_plugin.on_unload.assert_called()

    def test_broadcast_event(self):
        plugin = PluginWithEvents(mock.Mock())
        plugin.handle_event = mock.Mock()
        self.object.plugins = [plugin]
        self.object.broadcast_event(test_event_type, test_payload['data'])
        plugin.handle_event.assert_called_with(test_event_type, test_payload['data'])
