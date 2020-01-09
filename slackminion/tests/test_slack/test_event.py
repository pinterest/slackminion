from unittest import mock
from slackminion.slack import SlackEvent, SlackChannel, SlackGroup, SlackIM, SlackUser
from slackminion.tests.fixtures import *

test_im_id = 'D12345678'

# channel_id, channel_class
test_event_data = [
    (test_channel_id, SlackChannel),
    (test_group_id, SlackGroup),
    (test_im_id, SlackIM),
]

test_payload = {
    'rtm_client': mock.Mock(),
    'web_client': mock.Mock(),
    'data': {},
}


class TestSlackEvent(unittest.TestCase):

    def test_init(self):
        event = SlackEvent('test')
        assert event._user is None
        assert event._channel is None

    def test_init_user(self):
        test_payload['data'] = {'user': test_user_id}
        event = SlackEvent('user', **test_payload)
        assert isinstance(event.user, SlackUser)
        assert event.channel is None

    def test_init_user_slackuser(self):
        test_payload['data'] = {'user': SlackUser(test_user_id)}
        event = SlackEvent('message', **test_payload)
        assert isinstance(event.user, SlackUser)
        assert event.channel is None

    def test_init_channel(self):
        for channel_id, channel_class in test_event_data:
            test_payload['data'] = {'channel': channel_id}
            event = SlackEvent('channel', **test_payload)
            assert event.user is None
            assert isinstance(event.channel, channel_class)

    def test_init_channel_slackchannel(self):
        for channel_id, channel_class in test_event_data:
            test_payload['data'] = {'channel': channel_class(channel_id)}
            event = SlackEvent('channel', **test_payload)
            self.assertIsNone(event.user)
            self.assertIsInstance(event.channel, channel_class)
