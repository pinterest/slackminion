import pytest

from slackminion.plugin import BasePlugin


def dummy_func(self):
    self.xyzzy = True


class TestBasePlugin(object):

    def setup(self):
        self.object = BasePlugin(None)
        self.timer_started = False

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

    def test_start_timer(self, monkeypatch):
        def safe_start(self):
            assert self.interval == 30
            assert isinstance(self.args[1][0][0], TestBasePlugin)
            self.args[1][0][0].timer_started = True

        monkeypatch.setattr('threading.Thread.start', safe_start)
        self.object.start_timer(30, lambda: None, (self,))
        assert self.timer_started

    def test_stop_timer(self, monkeypatch):
        def safe_start(self):
            pass

        def safe_cancel(self):
            pass

        monkeypatch.setattr('threading.Thread.start', safe_start)
        monkeypatch.setattr('threading._Timer.cancel', safe_cancel)
        self.object.start_timer(30, dummy_func, self.object)
        assert dummy_func in self.object._timer_callbacks
        self.object.stop_timer(dummy_func)
        assert dummy_func not in self.object._timer_callbacks

    def test_run_timer(self, monkeypatch):
        def safe_start(self):
            self.function(*self.args)

        monkeypatch.setattr('threading.Thread.start', safe_start)
        self.object.start_timer(30, dummy_func, self.object)
        assert hasattr(self.object, 'xyzzy')
