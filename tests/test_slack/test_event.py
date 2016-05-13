import pytest

from slackminion.slack import SlackEvent, SlackChannel, SlackGroup, SlackIM, SlackUser
from slackminion.utils.test_helpers import *

test_im_id = 'D12345678'


# channel_id, channel_class
test_event_data = [
    (test_channel_id, SlackChannel),
    (test_group_id, SlackGroup),
    (test_im_id, SlackIM),
]


class TestSlackEvent(object):

    def test_init(self):
        event = SlackEvent()
        assert event._user is None
        assert event._channel is None

    def test_init_user(self):
        e = {'user': test_user_id}
        event = SlackEvent(**e)
        assert isinstance(event.user, SlackUser)
        assert event.channel is None

    def test_init_user_slackuser(self):
        e = {'user': SlackUser(test_user_id)}
        event = SlackEvent(**e)
        assert isinstance(event.user, SlackUser)
        assert event.channel is None

    @pytest.mark.parametrize('channel_id,channel_class', test_event_data)
    def test_init_channel(self, channel_id, channel_class):
        e = {'channel': channel_id}
        event = SlackEvent(**e)
        assert event.user is None
        assert isinstance(event.channel, channel_class)

    @pytest.mark.parametrize('channel_id,channel_class', test_event_data)
    def test_init_channel_slackchannel(self, channel_id, channel_class):
        e = {'channel': channel_class(channel_id)}
        event = SlackEvent(**e)
        assert event.user is None
        assert isinstance(event.channel, channel_class)
