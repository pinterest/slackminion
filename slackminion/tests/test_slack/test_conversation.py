from slackminion.tests.fixtures import *
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
TEST_CONVERSATION_UNNAMED = {
    'id': 'C02KT31H9GX',
    'is_channel': True,
    'is_group': False,
    'is_im': False,
    'is_mpim': False,
    'is_private': False,
    'topic': {'value': '', 'creator': '', 'last_set': 0},
    'priority': 0
}


class TestConversation(unittest.TestCase):

    def setUp(self):
        self.api_client = mock.Mock()
        self.object = SlackConversation(TEST_CONVERSATION, self.api_client)
        self.assertEqual(self.object.conversation, TEST_CONVERSATION)

    def test_missing_names(self):
        conversation = SlackConversation(TEST_CONVERSATION_UNNAMED, self.api_client)
        expected_names = []
        self.assertEqual(conversation.all_names, expected_names)

        new_name = TEST_CONVERSATION.get('name')
        TEST_CONVERSATION_UNNAMED['name'] = new_name
        conversation = SlackConversation(TEST_CONVERSATION_UNNAMED, self.api_client)
        expected_names = [new_name]
        self.assertEqual(conversation.all_names, expected_names)

        normalized_name = TEST_CONVERSATION.get('name_normalized')
        TEST_CONVERSATION_UNNAMED['name_normalized'] = normalized_name
        conversation = SlackConversation(TEST_CONVERSATION_UNNAMED, self.api_client)
        expected_names = [new_name, normalized_name]
        self.assertEqual(conversation.all_names, expected_names)

        previous_names = TEST_CONVERSATION.get('previous_names')
        TEST_CONVERSATION_UNNAMED['previous_names'] = previous_names
        conversation = SlackConversation(TEST_CONVERSATION_UNNAMED, self.api_client)
        expected_names = [new_name, normalized_name] + previous_names
        self.assertEqual(conversation.all_names, expected_names)

    def test_all_names(self):
        expected_names = [TEST_CONVERSATION['name'], TEST_CONVERSATION['name_normalized']] \
                         + TEST_CONVERSATION['previous_names']
        self.assertEqual(self.object.all_names, expected_names)

    def test_topic(self):
        self.assertEqual(self.object.topic, TEST_CONVERSATION['topic']['value'])
        new_topic = 'new topic'
        self.object.topic = new_topic
        self.assertEqual(self.object.topic, new_topic)
        self.api_client.conversations_setTopic.assert_called_with(channel=self.object.id, topic=new_topic)

    def test_getattr_accessor(self):
        self.assertEqual(self.object.is_private, TEST_CONVERSATION['is_private'])

    def test_channel_id(self):
        self.assertEqual(self.object.channel, TEST_CONVERSATION['id'])
        self.assertEqual(self.object.channel_id, TEST_CONVERSATION['id'])

    @async_test
    async def test_load_conversation(self):
        self.api_client.conversations_info = AsyncMock()
        self.api_client.conversations_info.coro.return_value = {'channel': TEST_CONVERSATION}
        self.object.conversation = {}
        await self.object.load(TEST_CONVERSATION['id'])
        self.api_client.conversations_info.assert_called_with(channel=TEST_CONVERSATION['id'])
        self.assertEqual(self.object.conversation, TEST_CONVERSATION)

    @async_test
    async def test_load_conversation_no_data(self):
        self.api_client.conversations_info = AsyncMock()
        self.api_client.conversations_info.coro.return_value = None
        self.object.conversation = {}
        with self.assertRaises(RuntimeError):
            await self.object.load(TEST_CONVERSATION['id'])

    def test_load_extra_attributes(self):
        self.object.conversation = {'id': TEST_CONVERSATION['id']}
        self.api_client.conversations_info.return_value = {'channel': TEST_CONVERSATION}
        self.object._load_extra_attributes()
        print(self.api_client.mock_calls)
        self.api_client.conversations_info.assert_called_with(channel=self.object.channel_id)
        self.assertEqual(self.object.conversation, TEST_CONVERSATION)

    def test_misc_methods(self):
        self.assertEqual(self.object.get_channel(), self.object)
        self.assertEqual(self.object.formatted_name, f'<#{self.object.id}|{self.object.name}>')
        self.assertEqual(f'{self.object}', self.object.formatted_name)
