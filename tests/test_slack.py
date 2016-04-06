import pytest
from slackminion.slack import SlackEvent, SlackUser, SlackChannel


class MockSlackAPIConnection(object):
    def __init__(self, channels=None, api_calls=None):
        self.server = MockSlackServer(channels)
        self._api_calls = api_calls

    def api_call(self, name, user):
        return self._api_calls[name]


class MockSlackServer(object):
    def __init__(self, channels):
        self.channels = MockSlackServerChannels(channels)


class MockSlackServerChannels(object):
    def __init__(self, channels):
        self._channels = channels

    def find(self, channelid):
        return MockSlackServerResponse(channelid, self._channels[channelid])


class MockSlackServerResponse(object):
    def __init__(self, channelid, name):
        self.channelid = channelid
        self.name = name

test_channels = {
    'C123': 'test_channel'
}

api_calls = {
    'users.info': {
        'user': {
            'name': 'testuser'
        }
    }
}

test_event = {
    'user': 'U123',
    'channel': 'C123',
}


class TestSlackChannel(object):
    def test_channel_property(self):
        sc = MockSlackAPIConnection(test_channels)
        o = SlackChannel('C123', sc)
        assert o.channel == 'test_channel'

    def test_channel_str(self):
        sc = MockSlackAPIConnection(test_channels)
        o = SlackChannel('C123', sc)
        assert str(o) == '<#C123|test_channel>'

    def test_channel_repr(self):
        sc = MockSlackAPIConnection(test_channels)
        o = SlackChannel('C123', sc)
        assert repr(o) == 'C123'


class TestSlackUser(object):
    def test_username_property(self):
        sc = MockSlackAPIConnection(api_calls=api_calls)
        o = SlackUser('U123', sc)
        assert o.username == 'testuser'

    def test_username_str(self):
        sc = MockSlackAPIConnection(api_calls=api_calls)
        o = SlackUser('U123', sc)
        assert str(o) == '<@U123|testuser>'

    def test_username_repr(self):
        sc = MockSlackAPIConnection(api_calls=api_calls)
        o = SlackUser('U123', sc)
        assert repr(o) == 'U123'


class TestSlackEvent(object):
    def test_channel_property(self):
        sc = MockSlackAPIConnection(test_channels)
        o = SlackEvent(sc, **test_event)
        assert o.channel.channel == 'test_channel'

    def test_user_property(self):
        sc = MockSlackAPIConnection(api_calls=api_calls)
        o = SlackEvent(sc, **test_event)
        assert o.user.username == 'testuser'
