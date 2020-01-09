import slack

from slackminion.slack import SlackUser
from slackminion.tests.fixtures import *

str_format = '<@{id}|{name}>'

test_user_mapping = []


class TestSlackUser(object):

    def setup(self):
        sc = mock.Mock()
        self.object = SlackUser(test_user_id, sc=sc)

    def teardown(self):
        self.object = None

    def test_init(self):
        assert self.object.id == test_user_id

    def test_userid(self):
        assert self.object.userid == test_user_id

    def test_username(self):
        class resp(object):
            id = test_user_id
            name = test_user_name
        self.object._sc.server.users.find.return_value = resp
        assert self.object.username == test_user_name

    def test_get_user(self):
        user = SlackUser.get_user(self.object._sc, test_user_name)
        assert isinstance(user, SlackUser)


def test_get_user_none():
    mock_sc = mock.Mock()
    mock_sc.server.users.find.return_value = None
    user = SlackUser.get_user(mock_sc, 'doesnotexist')
    assert user is None
