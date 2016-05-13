from slackclient._channel import Channel
from slackclient._user import User
from slackclient._util import SearchList

from slackminion.slack import SlackEvent

test_channel_id = 'C12345678'
test_channel_name = 'testchannel'
test_group_id = 'G12345678'
test_group_name = 'testgroup'
test_user_id = 'U12345678'
test_user_name = 'testuser'


class DummyServer(object):
    def __init__(self):
        self.channels = SearchList()
        self.users = SearchList()


class DummySlackConnection(object):
    def __init__(self):
        self.server = DummyServer()
        self.server.channels.append(Channel(None, test_channel_name, test_channel_id))
        self.server.channels.append(Channel(None, test_group_name, test_group_id))
        self.server.users.append(User(None, test_user_name, test_user_id, test_user_name, None))
        self.topic = 'Test Topic'

    def api_call(self, name, *args, **kwargs):
        if 'setTopic' in name:
            self.topic = kwargs['topic']
        api_responses = {
            'channels.info': {
                'channel': {
                    'name': test_channel_name,
                    'creator': test_user_id,
                    'topic': {
                        'value': self.topic,
                    },
                },
            },
            'channels.setTopic': {
                'topic': self.topic,
            },
            'groups.info': {
                'group': {
                    'name': test_group_name,
                    'creator': test_user_id,
                    'topic': {
                        'value': self.topic,
                    },
                },
            },
            'groups.setTopic': {
                'topic': self.topic,
            },
            'users.info': {
                'user': {
                    'id': test_user_id,
                    'name': test_user_name,
                },
            }
        }
        return api_responses[name]


def get_test_event():
    return SlackEvent(sc=DummySlackConnection(), user=test_user_id, channel=test_channel_id)
