import pytest

from slackminion.plugin import BasePlugin, cmd

from .bot import DummyBot
from .slack import DummySlackConnection

EXPECTED_PLUGIN_METHODS = [
    'on_connect',
    'on_load',
    'on_unload',
]


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


class BasicPluginTest(object):
    PLUGIN_CLASS = None
    BASE_METHODS = ['on_load', 'on_connect', 'on_unload']
    ADMIN_COMMANDS = []

    def setup(self):
        self.bot = DummyBot()
        self.bot.sc = DummySlackConnection()
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
