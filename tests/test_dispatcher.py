import pytest

from slackminion.dispatcher import MessageDispatcher
from slackminion.exceptions import DuplicateCommandError
from slackminion.plugin import BasePlugin, cmd
from slackminion.slack import SlackChannel, SlackEvent


class DummyPlugin(BasePlugin):
    @cmd(aliases='xyz')
    def abc(self, msg, args):
        pass


class TestDispatcher(object):
    def setup(self):
        self.object = MessageDispatcher()
        self.p = DummyPlugin(None)

    def teardown(self):
        self.object = None

    def test_register_plugin(self):
        self.object.register_plugin(self.p)

    def test_register_duplicate_plugin(self):
        self.object.register_plugin(self.p)
        with pytest.raises(DuplicateCommandError) as e:
            self.object.register_plugin(self.p)
        assert 'abc' in str(e)

    def test_get_command(self):
        self.object.register_plugin(self.p)
        assert self.object._get_command('!abc', None).method == self.p.abc

    def test_get_invalid_command(self):
        self.object.register_plugin(self.p)
        with pytest.raises(KeyError):
            self.object._get_command('!def', None)

    def test_parse_message(self):
        e = SlackEvent(text='Hello world')
        assert self.object._parse_message(e) == ['Hello', 'world']

    def test_ignore_channel(self):
        assert self.object.ignore('testchannel') is True
        assert 'testchannel' in self.object.ignored_channels

    def test_unignore_channel(self):
        assert self.object.ignore('testchannel') is True
        assert self.object.unignore('testchannel') is True
        assert 'testchannel' not in self.object.ignored_channels

    def test_unignore_nonignored_channel(self):
        self.object.unignore('testchannel') is False
        assert 'testchannel' not in self.object.ignored_channels

    def test_ignore_duplicate_channel(self):
        assert self.object.ignore('testchannel') is True
        assert 'testchannel' in self.object.ignored_channels
        assert self.object.ignore('testchannel') is False
        assert len(self.object.ignored_channels) == 1

    def test_ignore_slackchannel(self):
        c = SlackChannel('CTEST')
        c._channel = 'testchannel'
        assert self.object.ignore(c) is True
        assert 'testchannel' in self.object.ignored_channels
        assert self.object._is_channel_ignored(self.p.abc, c) is True

    def test_unignore_slackchannel(self):
        c = SlackChannel('CTEST')
        c._channel = 'testchannel'
        assert self.object.ignore(c) is True
        assert self.object.unignore(c) is True
        assert 'testchannel' not in self.object.ignored_channels
        assert self.object._is_channel_ignored(self.p.abc, c) is False
