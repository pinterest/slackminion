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

    def test_init_channel(self):
        event = SlackEvent('channel', **self.test_payload)
        assert event.user_id is None
        assert isinstance(event.channel, SlackConversation)

