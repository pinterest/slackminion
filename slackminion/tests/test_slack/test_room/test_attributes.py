from slackminion.slack.room.attributes import SlackRoomAttribute, SlackRoomTopic


class AttributeHarness(object):

    test_attr = SlackRoomAttribute()

    def __init__(self):
        self.test_attr = None

    def _load_extra_attributes(self):
        self.test_attr = 'Hello World'


class TopicHarness(object):

    test_topic = SlackRoomTopic()

    def __init__(self):
        self.test_topic = None
        self.topic_set = False

    def _load_extra_attributes(self):
        self.test_topic = 'A test topic'

    def set_topic(self, value):
        self.topic_set = True


class TestRoomAttributes(object):
    def setup(self):
        self.object = AttributeHarness()

    def teardown(self):
        self.object = None

    def test_set_attr(self):
        self.object.test_attr = 'xyzzy'
        assert self.object.test_attr == 'xyzzy'

    def test_get_attr(self):
        assert self.object.test_attr == 'Hello World'


class TestRoomTopic(object):
    def setup(self):
        self.object = TopicHarness()

    def teardown(self):
        self.object = None

    def test_set_topic(self):
        self.object.test_topic = 'Something'
        assert self.object.topic_set is False
        assert self.object.test_topic == 'Something'
        self.object.test_topic = 'Something more'
        assert self.object.topic_set is True
        assert self.object.test_topic == 'Something more'

    def test_get_topic(self):
        assert self.object.test_topic == 'A test topic'
