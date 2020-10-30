from slackminion.exceptions import DuplicateCommandError
from slackminion.tests.fixtures import *
from slackminion.dispatcher import MessageDispatcher
from copy import deepcopy

test_data_mapping = []


class TestDispatcher(unittest.TestCase):

    @mock.patch('slackminion.slack.SlackUser')
    def setUp(self, mock_user):
        mock_user.return_value = test_user
        self.dispatcher = MessageDispatcher()
        self.p = DummyPlugin(None)
        self.test_payload = deepcopy(test_payload)

    def tearDown(self):
        self.dispatcher = None
        self.test_payload = None

    def test_register_plugin(self):
        self.dispatcher.register_plugin(self.p)

    def test_register_duplicate_plugin(self):
        self.dispatcher.register_plugin(self.p)
        with self.assertRaises(DuplicateCommandError) as e:
            self.dispatcher.register_plugin(self.p)
            self.assertIn('abc', str(e))

    def test_get_command(self):
        self.dispatcher.register_plugin(self.p)
        method = self.dispatcher._get_command('!abc', None).method
        assert method == self.p.abc
        assert method(None, None) == 'abcba'

    def test_get_invalid_command(self):
        self.dispatcher.register_plugin(self.p)
        with self.assertRaises(KeyError):
            self.dispatcher._get_command('!def', None)

    def test_parse_message(self):
        e = SlackEvent(event_type='message', **{'data': {'text': 'Hello world'}})
        assert self.dispatcher._parse_message(e) == ['Hello', 'world']

    def test_parse_message_unicode(self):
        e = SlackEvent(event_type='message', **{'data': {'text': 'Hello\xa0world'}})
        assert self.dispatcher._parse_message(e) == ['Hello', 'world']

    @async_test
    async def test_strip_formatting(self):
        test_string = "!stripformat <@U123456> check <#C123456|test-channel> has <https://www.pinterest.com|www.pinterest.com>"
        expected_response = "@U123456 check #test-channel has www.pinterest.com"
        e = SlackEvent(event_type="message", **{"data": {"text": test_string}})
        e.user = mock.Mock()
        e.channel = test_conversation
        self.dispatcher.register_plugin(self.p)
        cmd, output, cmd_opts = await self.dispatcher.push(e)
        assert cmd_opts.get("strip_formatting") is True
        self.assertEqual(expected_response, output)

    def test_unignore_nonignored_channel(self):
        c = SlackConversation(conversation=test_channel, api_client=test_payload.get('api_client'))
        self.assertFalse(self.dispatcher.unignore(c))
        assert 'testchannel' not in self.dispatcher.ignored_channels

    def test_ignore_duplicate_channel(self):
        c = SlackConversation(conversation=test_channel, api_client=test_payload.get('api_client'))
        assert self.dispatcher.ignore(c) is True
        assert c.name in self.dispatcher.ignored_channels
        assert self.dispatcher.ignore(c) is False
        assert len(self.dispatcher.ignored_channels) == 1

    def test_ignore_slackchannel(self):
        c = SlackConversation(conversation=test_channel, api_client=test_payload.get('api_client'))
        c.name = 'testchannel'
        assert self.dispatcher.ignore(c) is True
        assert 'testchannel' in self.dispatcher.ignored_channels
        assert self.dispatcher._is_channel_ignored(self.p.abc, c) is True

    def test_unignore_slackchannel(self):
        c = SlackConversation(conversation=test_channel, api_client=test_payload.get('api_client'))
        self.assertTrue(self.dispatcher.ignore(c))
        self.assertTrue(self.dispatcher.unignore(c))
        self.assertNotIn(test_channel.get('name'), self.dispatcher.ignored_channels)
        self.assertFalse(self.dispatcher._is_channel_ignored(self.p.abc, c))

    @async_test
    async def test_push(self):
        self.dispatcher.register_plugin(self.p)
        self.test_payload['data'].update({'text': '!abc'})
        e = SlackEvent(event_type="message", **self.test_payload)
        e.user = mock.Mock()
        e.channel = test_conversation
        cmd, output, cmd_opts = await self.dispatcher.push(e)
        assert cmd == '!abc'
        assert output == 'abcba'
        assert type(cmd_opts) == dict
        assert ('reply_in_thread' in list(cmd_opts.keys())) is True
        assert ('reply_broadcast' in list(cmd_opts.keys())) is True
        assert cmd_opts.get('reply_broadcast') is False
        assert cmd_opts.get('reply_in_thread') is False

    @async_test
    async def test_push_alias(self):
        self.dispatcher.register_plugin(self.p)
        self.test_payload['data'].update({'text': '!bca'})
        e = SlackEvent(event_type="message", **self.test_payload)
        e.user = mock.Mock()
        e.channel = test_conversation
        cmd, output, cmd_opts = await self.dispatcher.push(e)
        assert cmd == '!bca'
        assert output == 'abcba'
        assert type(cmd_opts) == dict
        assert ('reply_in_thread' in list(cmd_opts.keys())) is True
        assert ('reply_broadcast' in list(cmd_opts.keys())) is True
        assert cmd_opts.get('reply_broadcast') is False
        assert cmd_opts.get('reply_in_thread') is False

    @async_test
    async def test_push_to_thread(self):
        self.dispatcher.register_plugin(self.p)
        self.test_payload['data'].update({'text': '!efg'})
        e = SlackEvent(event_type="message", **self.test_payload)
        e.channel = test_conversation
        e.user = mock.Mock()
        cmd, output, cmd_opts = await self.dispatcher.push(e)
        assert cmd == '!efg'
        assert output == 'efgfe'
        assert type(cmd_opts) == dict
        assert ('reply_in_thread' in list(cmd_opts.keys())) is True
        assert ('reply_broadcast' in list(cmd_opts.keys())) is True
        assert cmd_opts.get('reply_broadcast') is False
        assert cmd_opts.get('reply_in_thread') is True

    @async_test
    async def test_push_to_thread_with_broadcast(self):
        self.dispatcher.register_plugin(self.p)
        payload = dict(self.test_payload)
        payload['data'].update({'text': '!hij'})
        e = SlackEvent(event_type="message", **self.test_payload)
        e.user = mock.Mock()
        e.channel = test_conversation
        cmd, output, cmd_opts = await self.dispatcher.push(e)
        assert cmd == '!hij'
        assert output == 'hijih'
        assert type(cmd_opts) == dict
        assert ('reply_in_thread' in list(cmd_opts.keys())) is True
        assert ('reply_broadcast' in list(cmd_opts.keys())) is True
        assert cmd_opts.get('reply_broadcast') is True
        assert cmd_opts.get('reply_in_thread') is True

    @async_test
    async def test_push_not_command(self):
        payload = dict(self.test_payload)
        payload['data'].update({'text': 'Not a command'})
        e = SlackEvent(event_type="message", **payload)
        assert await self.dispatcher.push(e) == (None, None, None)

    @async_test
    async def test_push_message_replied_event(self):
        payload = dict(self.test_payload)
        payload['data'].update({'subtype': 'message_replied'})
        e = SlackEvent(event_type="message", **payload)
        assert await self.dispatcher.push(e) == (None, None, None)

    @async_test
    async def test_push_no_user(self):
        self.dispatcher.register_plugin(self.p)
        payload = dict(self.test_payload)
        payload['data'].update({'subtype': 'message_replied'})
        payload['data'].pop('user')
        e = SlackEvent(event_type="message", **payload)
        assert await self.dispatcher.push(e) == (None, None, None)

    @async_test
    async def test_push_ignored_channel(self):
        c = SlackConversation(conversation=test_channel, api_client=test_payload.get('api_client'))
        self.dispatcher.ignore(c)
        self.dispatcher.register_plugin(self.p)
        self.dispatcher._is_channel_ignored = mock.Mock(return_value=True)
        self.test_payload['data'].update({'text': '!abc', 'user': test_user_id, 'channel': test_channel_id})
        e = SlackEvent(event_type='message', **self.test_payload)
        e.channel = test_conversation
        e.user = mock.Mock()
        assert await self.dispatcher.push(e) == ('_ignored_', '', None)

    @async_test
    async def test_async_cmd(self):
        self.dispatcher.register_plugin(self.p)
        payload = dict(self.test_payload)
        payload['data'].update({'text': '!asyncabc'})
        e = SlackEvent(event_type="message", **self.test_payload)
        e.user = mock.Mock()
        e.channel = test_conversation
        cmd, output, cmd_opts = await self.dispatcher.push(e)
        assert cmd == '!asyncabc'
        assert output == 'asyncabc response'
        assert type(cmd_opts) == dict
        assert ('reply_in_thread' in list(cmd_opts.keys())) is True
        assert ('reply_broadcast' in list(cmd_opts.keys())) is True
        assert ('parse' in list(cmd_opts.keys())) is True
        assert cmd_opts.get('reply_broadcast') is True
        assert cmd_opts.get('reply_in_thread') is True
        assert cmd_opts.get('parse') is None

    @async_test
    async def test_async_cmd_parse(self):
        self.dispatcher.register_plugin(self.p)
        payload = dict(self.test_payload)
        payload['data'].update({'text': '!asyncparse'})
        e = SlackEvent(event_type="message", **self.test_payload)
        e.user = mock.Mock()
        e.channel = test_conversation
        cmd, output, cmd_opts = await self.dispatcher.push(e)
        assert cmd == '!asyncparse'
        assert output == 'async parse command #parse'
        assert type(cmd_opts) == dict
        assert ('reply_in_thread' in list(cmd_opts.keys())) is True
        assert ('reply_broadcast' in list(cmd_opts.keys())) is True
        assert ('parse' in list(cmd_opts.keys())) is True
        assert cmd_opts.get('reply_broadcast') is False
        assert cmd_opts.get('reply_in_thread') is False
        assert cmd_opts.get('parse') is True

if __name__ == "__main__":
    unittest.main()
