import unittest
from unittest import mock

from slackminion.slack.conversation import SlackConversation

TEST_CONVERSATION = {
    'id': 'C02KT31H9GX',
    'name': 'TEST-channel',
    'is_channel': True,
    'is_group': False,
    'is_im': False,
    'is_mpim': False,
    'is_private': False,
    'name_normalized': 'test-channel',
    'topic': {'value': '', 'creator': '', 'last_set': 0},
    'previous_names': ['old-test-channel-name', 'some-other-name'],
    'priority': 0
}


class TestConversation(unittest.TestCase):

    def setUp(self):
        self.api_client = mock.Mock()
        self.object = SlackConversation(TEST_CONVERSATION, self.api_client)

    def test_all_names(self):
        expected_names = [TEST_CONVERSATION['name'], TEST_CONVERSATION['name_normalized']] \
                         + TEST_CONVERSATION['previous_names']
        self.assertEqual(self.object.all_names, expected_names)

    def test_topic(self):
        self.assertEqual(self.object.topic, TEST_CONVERSATION['topic']['value'])

    def test_accessor(self):
        self.assertEqual(self.object.is_private, TEST_CONVERSATION['is_private'])
