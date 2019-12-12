import pytest

from slackminion.slack.room.room import SlackChannel, SlackGroup
from slackminion.tests.fixtures import *

str_format = '<#{id}|{name}>'

test_channel_mapping = {
    test_channel_name: test_channel_id,
    test_group_name: test_group_id,
}


@pytest.fixture(autouse=True)
def patch_slackclient_channels_find(monkeypatch):
    def find(self, name):
        class Response(object):
            def __init__(self, name):
                self.id = test_channel_mapping[name]
                self.name = name

        if name in test_channel_mapping:
            resp = Response(name)
            return resp
        return None

    monkeypatch.setattr('slackclient.util.SearchList.find', find)


class TSlackRoom(object):
    room_class = None
    test_id = None
    test_room_name = None

    def setup(self):
        self.object = self.room_class(self.test_id, sc=DummySlackConnection())

    def teardown(self):
        self.object = None

    def test_init(self):
        assert self.object.id == self.test_id
        for attr in self.room_class.BASE_ATTRIBUTES + self.room_class.EXTRA_ATTRIBUTES:
            if isinstance(attr, tuple):
                attr, attr_class = attr
            assert hasattr(self.object, attr)

    def test_channelid(self):
        assert self.object.channelid == self.test_id

    def test_channel(self):
        self.object.name = self.test_room_name
        assert self.object.channel == self.test_room_name

    def test_name(self):
        self.object.name = self.test_room_name
        assert self.object.name == self.test_room_name

        self.object = SlackChannel(self.test_id, name=self.test_room_name, sc=DummySlackConnection())
        assert self.object.name == self.test_room_name

    def test_str(self):
        assert str(self.object) == str_format.format(id=self.test_id, name=self.test_room_name)

    def test_repr(self):
        assert repr(self.object) == self.test_id

    def test_get_channel(self):
        channel = self.room_class.get_channel(SlackClient('xxx'), self.test_room_name)
        assert isinstance(channel, self.room_class)

    def test_set_topic(self, monkeypatch):
        api_name = self.room_class.API_PREFIX + '.setTopic'

        def api_call(self, name, *args, **kwargs):
            if 'setTopic' in name:
                assert name == api_name
            return orig_api_call(self, name, *args, **kwargs)

        orig_api_call = DummySlackConnection.api_call
        monkeypatch.setattr(DummySlackConnection, 'api_call', api_call)
        assert self.object.topic == 'Test Topic'
        self.object.topic = 'A new topic'
        assert self.object.topic == 'A new topic'


class TestSlackChannel(TSlackRoom):
    room_class = SlackChannel
    test_id = test_channel_id
    test_room_name = test_channel_name


class TestSlackGroup(TSlackRoom):
    room_class = SlackGroup
    test_id = test_group_id
    test_room_name = test_group_name


def test_get_channel_none():
    channel = SlackChannel.get_channel(SlackClient('xxx'), 'doesnotexist')
    assert channel is None
