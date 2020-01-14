from slackminion.tests.fixtures import *
import unittest
from unittest import mock


class TestSlackUser(unittest.TestCase):

    def setUp(self):
        self.api_client = mock.Mock()

    def tearDown(self):
        self.api_client = None

    def test_init_with_userid(self):
        self.api_client.users_info.return_value = test_user_response
        user = SlackUser(user_id=test_user_id, api_client=self.api_client)
        self.api_client.users_info.assert_called_with(test_user_id)
        self.assertEqual(user.id, test_user_id)
        self.assertEqual(user.user_id, test_user_id)
        self.assertEqual(user.userid, test_user_id)
        self.assertEqual(user.username, test_user_name)

    def test_init_with_user_info(self):
        self.api_client.users_info.return_value = None
        user = SlackUser(user_info=test_user_response['user'], api_client=self.api_client)
        print(user._user_id)
        self.assertEqual(user.id, test_user_id)
        self.assertEqual(user.user_id, test_user_id)
        self.assertEqual(user.userid, test_user_id)
        self.assertEqual(user.username, test_user_name)

    def test_get_user_none(self):
        self.api_client.users_info.return_value = None
        with self.assertRaises(RuntimeError):
            user = SlackUser(user_id='doesnotexist', api_client=self.api_client)
