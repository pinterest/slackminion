from unittest import mock
from slackminion.slack.conversation import SlackConversation
from slackminion.tests.fixtures import *

test_im_id = 'D12345678'

# channel_id, channel_class
test_event_data = [
    (test_channel_id, SlackConversation),
    (test_group_id, SlackConversation),
    (test_im_id, SlackConversation),
]

test_payload = {
    'rtm_client': mock.Mock(),
    'web_client': mock.Mock(),
    'data': {
        'channel': test_channel_id,
    },
}


class TestSlackEvent(unittest.TestCase):
    def setUp(self):
        self.test_payload = test_payload

    def tearDown(self) -> None:
        self.test_payload = None

    def test_init(self):
        event = SlackEvent(test_event_type, **self.test_payload)
        self.assertEqual(event.event_type, test_event_type)
        self.assertEqual(event.rtm_client, self.test_payload.get('rtm_client'))
        self.assertEqual(event.web_client, self.test_payload.get('web_client'))
        self.assertEqual(event.data, self.test_payload.get('data'))

    def test_init_user(self):
        self.test_payload['data'].update({'user': test_user_id})
        event = SlackEvent('message', **self.test_payload)
        self.assertEqual(event.user_id, test_user_id)

    def test_init_channel_no_user(self):
        event = SlackEvent('channel', **self.test_payload)
        self.assertIsNone(event.user_id)
        self.assertEqual(event.channel_id, test_payload.get('data').get('channel'))

    def test_init_channel_with_user(self):
        self.test_payload['data'].update({'user': test_user_id})
        event = SlackEvent('channel', **self.test_payload)
        self.assertEqual(event.channel_id, test_payload.get('data').get('channel'))
        self.assertEqual(event.user_id, test_payload.get('data').get('user'))

    def test_get_ts(self):
        self.test_payload['data'].update({'ts': test_thread_ts})
        event = SlackEvent('channel', **self.test_payload)
        self.assertEqual(event.ts, test_thread_ts)

    def test_get_thread_ts(self):
        self.test_payload['data'].update({'thread_ts': test_thread_ts})
        event = SlackEvent('channel', **self.test_payload)
        self.assertEqual(event.thread_ts, test_thread_ts)

    def test_get_text(self):
        self.test_payload['data'].update({'text': test_text})
        event = SlackEvent('channel', **self.test_payload)
        self.assertEqual(event.text, test_text)

    def test_get_text_2(self):
        self.test_payload['data'].update({'message': {'text': test_text}})
        event = SlackEvent('channel', **self.test_payload)
        self.assertEqual(event.text, test_text)
