from slackminion.slack.room.im import SlackIM

test_id = 'U12345678'
str_format = '<#{id}|{id}>'


class TestSlackIM(object):
    def setup(self):
        self.object = SlackIM(test_id)

    def teardown(self):
        self.object = None

    def test_init(self):
        assert self.object.id == test_id
        assert self.object.is_im is True

    def test_name(self):
        assert self.object.name == test_id

    def test_channel(self):
        assert self.object.channel == test_id

