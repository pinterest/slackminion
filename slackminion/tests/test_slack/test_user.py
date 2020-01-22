from slackminion.tests.fixtures import *
import unittest
from unittest import mock


class TestSlackUser(unittest.TestCase):

    def setUp(self):
        self.api_client = mock.Mock()

    def tearDown(self):
        self.api_client = None

    @async_test
    async def test_init_with_userid(self):
        self.api_client.users_info = AsyncMock()
        self.api_client.users_info.coro.return_value = test_user_response
        user = SlackUser(user_id=test_user_id, api_client=self.api_client)
        await user.load()
        self.api_client.users_info.assert_called_with(user=test_user_id)
        self.assertEqual(user.id, test_user_id)
        self.assertEqual(user.user_id, test_user_id)
        self.assertEqual(user.userid, test_user_id)
        self.assertEqual(user.username, test_user_name)

    def test_init_with_user_info(self):
        self.api_client.users_info.return_value = None
        user = SlackUser(user_info=test_user_response['user'], api_client=self.api_client)
        self.assertEqual(user.id, test_user_id)
        self.assertEqual(user.user_id, test_user_id)
        self.assertEqual(user.userid, test_user_id)
        self.assertEqual(user.username, test_user_name)

    @async_test
    async def test_get_user_none(self):
        self.api_client.users_info = AsyncMock()
        self.api_client.users_info.coro.return_value = None
        with self.assertRaises(RuntimeError):
            user = SlackUser(user_id='doesnotexist', api_client=self.api_client)
            await user.load()
