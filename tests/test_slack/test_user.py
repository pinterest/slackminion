import pytest

from slackclient import SlackClient
from slackclient.user import User

from slackminion.slack import SlackUser
from slackminion.utils.test_helpers import *

str_format = '<@{id}|{name}>'

test_user_mapping = []


@pytest.fixture(autouse=True)
def patch_slackclient_channels_find(monkeypatch):
    test_user_mapping.append(User(None, test_user_name, test_user_id, test_user_name, None, test_user_email))

    def find(self, id):
        users = filter(lambda x: x == id, test_user_mapping)
        if len(users) > 0:
            return users[0]
        return None
    monkeypatch.setattr('slackclient.util.SearchList.find', find)


class TestSlackUser(object):

    def setup(self):
        self.object = SlackUser(test_user_id, sc=DummySlackConnection())

    def teardown(self):
        self.object = None

    def test_init(self):
        assert self.object.id == test_user_id

    def test_userid(self):
        assert self.object.userid == test_user_id

    def test_username(self):
        assert self.object.username == test_user_name

    def test_str(self):
        assert str(self.object) == str_format.format(id=test_user_id, name=test_user_name)

    def test_repr(self):
        assert repr(self.object) == test_user_id

    def test_get_user(self):
        user = SlackUser.get_user(DummySlackConnection(), test_user_name)
        assert isinstance(user, SlackUser)


def test_get_user_none():
    user = SlackUser.get_user(DummySlackConnection(), 'doesnotexist')
    assert user is None
