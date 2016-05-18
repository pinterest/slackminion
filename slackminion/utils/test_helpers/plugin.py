import pytest

from .bot import DummyBot
from .slack import DummySlackConnection

EXPECTED_PLUGIN_METHODS = [
    'on_connect',
    'on_load',
    'on_unload',
]


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
        from _pytest.monkeypatch import monkeypatch

        def called_func(*args, **kwargs):
            self.called[method] = True
        self.called[method] = False
        monkeypatch().setattr(method, called_func)
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
