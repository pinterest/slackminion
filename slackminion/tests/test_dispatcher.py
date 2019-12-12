from builtins import str

from slackminion.exceptions import DuplicateCommandError
from slackminion.tests.fixtures import *

test_data_mapping = []


class TestDispatcher(unittest.TestCase):
    def setUp(self):
        self.object = MessageDispatcher()
        self.p = DummyPlugin(None)

    def tearDown(self):
        self.object = None

    def test_register_plugin(self):
        self.object.register_plugin(self.p)

    def test_register_duplicate_plugin(self):
        self.object.register_plugin(self.p)
        with self.assertRaises(DuplicateCommandError) as e:
            self.object.register_plugin(self.p)
            self.assertIn('abc', str(e))

    def test_get_command(self):
        self.object.register_plugin(self.p)
        method = self.object._get_command('!abc', None).method
        assert method == self.p.abc
        assert method(None, None) == 'abcba'

    def test_get_invalid_command(self):
        self.object.register_plugin(self.p)
        with self.assertRaises(KeyError):
            self.object._get_command('!def', None)

    def test_parse_message(self):
        e = SlackEvent(event_type='message', **{'data': {'text': 'Hello world'}})
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
        e = SlackEvent(event_type="message", sc=mock.Mock(),
                       **{'data': {'text': '!abc', 'user': test_user_id, 'channel': test_channel_id}})
        cmd, output, cmd_opts = self.object.push(e)
        assert cmd == '!abc'
        assert output == 'abcba'
        assert type(cmd_opts) == dict
        assert ('reply_in_thread' in list(cmd_opts.keys())) is True
        assert ('reply_broadcast' in list(cmd_opts.keys())) is True
        assert cmd_opts.get('reply_broadcast') is False
        assert cmd_opts.get('reply_in_thread') is False

    def test_push_alias(self):
        self.object.register_plugin(self.p)
        e = SlackEvent(event_type="message", sc=mock.Mock(),
                       **{'data': {'text': '!bca', 'user': test_user_id, 'channel': test_channel_id}})
        cmd, output, cmd_opts = self.object.push(e)
        assert cmd == '!bca'
        assert output == 'abcba'
        assert type(cmd_opts) == dict
        assert ('reply_in_thread' in list(cmd_opts.keys())) is True
        assert ('reply_broadcast' in list(cmd_opts.keys())) is True
        assert cmd_opts.get('reply_broadcast') is False
        assert cmd_opts.get('reply_in_thread') is False

    def test_push_to_thread(self):
        self.object.register_plugin(self.p)
        e = SlackEvent(event_type="message", sc=mock.Mock(),
                       **{'data': {'text': '!efg', 'user': test_user_id, 'channel': test_channel_id}})
        cmd, output, cmd_opts = self.object.push(e)
        assert cmd == '!efg'
        assert output == 'efgfe'
        assert type(cmd_opts) == dict
        assert ('reply_in_thread' in list(cmd_opts.keys())) is True
        assert ('reply_broadcast' in list(cmd_opts.keys())) is True
        assert cmd_opts.get('reply_broadcast') is False
        assert cmd_opts.get('reply_in_thread') is True

    def test_push_to_thread_with_broadcast(self):
        self.object.register_plugin(self.p)
        e = SlackEvent(event_type="message", sc=mock.Mock(),
                       **{'data': {'text': '!hij', 'user': test_user_id, 'channel': test_channel_id}})
        cmd, output, cmd_opts = self.object.push(e)
        assert cmd == '!hij'
        assert output == 'hijih'
        assert type(cmd_opts) == dict
        assert ('reply_in_thread' in list(cmd_opts.keys())) is True
        assert ('reply_broadcast' in list(cmd_opts.keys())) is True
        assert cmd_opts.get('reply_broadcast') is True
        assert cmd_opts.get('reply_in_thread') is True

    def test_push_not_command(self):
        e = SlackEvent(event_type="message", sc=mock.Mock(), **{'data': {'text': 'Not a command'}})
        assert self.object.push(e) == (None, None, None)

    def test_push_message_replied_event(self):
        e = SlackEvent(event_type="message", sc=mock.Mock(), **{'data': {'subtype': 'message_replied'}})
        assert self.object.push(e) == (None, None, None)

    def test_push_no_user(self):
        self.object.register_plugin(self.p)
        e = SlackEvent(event_type="message", sc=mock.Mock(), **{'data': {'text': '!abc'}})
        assert self.object.push(e) == (None, None, None)

    def test_push_ignored_channel(self):
        c = SlackChannel('CTEST')
        c.name = 'testchannel'
        self.object.ignore(c)
        self.object.register_plugin(self.p)
        self.object._is_channel_ignored = mock.Mock(return_value=True)
        e = SlackEvent(event_type='message', sc=mock.Mock(),
                       **{'data': {'text': '!abc', 'user': test_user_id, 'channel': test_channel_id}})
        assert self.object.push(e) == ('_ignored_', '', None)
