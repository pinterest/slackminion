from slackminion.slack import SlackConversation
from slackminion.tests.fixtures import *

str_format = '<#{id}|{name}>'

test_channel_mapping = {
    test_channel_name: test_channel_id,
    test_group_name: test_group_id,
}


class TSlackRoom(object):
    room_class = None
    test_id = None
    test_room_name = None

    def setup(self):
        self.object = self.room_class(self.test_id, sc=mock.Mock())
        self.object._sc.api_call.return_value = {self.object.ATTRIBUTE_KEY: {}}

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

        self.object = SlackConversation(self.test_id, name=self.test_room_name, api_client=mock.Mock())
        assert self.object.name == self.test_room_name

    def test_get_channel(self):
        test_channel = mock.Mock()
        test_channel.id = self.test_id
        test_channel.name = self.test_room_name
        self.object.api_client.server.channels.find.return_value = test_channel
        channel = self.room_class.get_channel(self.object.api_client, self.test_room_name)
        assert isinstance(channel, self.room_class)

    def test_set_topic(self):
        api_name = self.room_class.API_PREFIX + '.setTopic'
        new_topic_name = 'A new topic'
        self.object.set_topic(new_topic_name)
        self.object.api_client.api_call.assert_called_with(api_name, channel=self.test_id, topic=new_topic_name)

