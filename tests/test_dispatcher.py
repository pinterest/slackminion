import pytest

from slackclient.channel import Channel
from slackclient.user import User
from slackminion.dispatcher import MessageDispatcher
from slackminion.exceptions import DuplicateCommandError
from slackminion.slack import SlackChannel
from slackminion.utils.test_helpers import *

test_data_mapping = []


@pytest.fixture(autouse=True)
def patch_slackclient_channels_find(monkeypatch):
    test_data_mapping.append(User(None, test_user_name, test_user_id, test_user_name, None, test_user_email))
    test_data_mapping.append(Channel(None, test_channel_name, test_channel_id, None))

    def find(self, id):
        res = filter(lambda x: x == id, test_data_mapping)
        if len(res) > 0:
            return res[0]
        return None
    monkeypatch.setattr('slackclient.util.SearchList.find', find)


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
        method = self.object._get_command('!abc', None).method
        assert method == self.p.abc
        assert method(None, None) == 'xyzzy'

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
        c.name = 'testchannel'
        assert self.object.ignore(c) is True
        assert 'testchannel' in self.object.ignored_channels
        assert self.object._is_channel_ignored(self.p.abc, c) is True

    def test_unignore_slackchannel(self):
        c = SlackChannel('CTEST')
        c.name = 'testchannel'
        assert self.object.ignore(c) is True
        assert self.object.unignore(c) is True
        assert 'testchannel' not in self.object.ignored_channels
        assert self.object._is_channel_ignored(self.p.abc, c) is False

    def test_push(self):
        self.object.register_plugin(self.p)
        e = SlackEvent(DummySlackConnection(), **{'text': '!abc', 'user': test_user_id, 'channel': test_channel_id})
        assert self.object.push(e) == ('!abc', 'xyzzy')

    def test_push_alias(self):
        self.object.register_plugin(self.p)
        e = SlackEvent(DummySlackConnection(), **{'text': '!xyz', 'user': test_user_id, 'channel': test_channel_id})
        assert self.object.push(e) == ('!xyz', 'xyzzy')

    def test_push_not_command(self):
        e = SlackEvent(DummySlackConnection(), **{'text': 'Not a command'})
        assert self.object.push(e) == (None, None)

    def test_push_message_replied_event(self):
        e = SlackEvent(DummySlackConnection(), **{'subtype': 'message_replied'})
        assert self.object.push(e) == (None, None)

    def test_push_no_user(self):
        self.object.register_plugin(self.p)
        e = SlackEvent(DummySlackConnection(), **{'text': '!abc'})
        assert self.object.push(e) == (None, None)

    def test_push_ignored_channel(self):
        c = SlackChannel('CTEST')
        c.name = 'testchannel'
        self.object.ignore(c)
        self.object.register_plugin(self.p)
        e = SlackEvent(DummySlackConnection(), **{'text': '!abc', 'user': test_user_id, 'channel': test_channel_id})
        assert self.object.push(e) == ('_ignored_', '')
