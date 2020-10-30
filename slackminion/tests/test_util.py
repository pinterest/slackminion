import unittest
from slackminion.utils.util import strip_formatting


class TestCase(unittest.TestCase):

    def test_strip_formatting(self):
        test_string = '<@U123456> check <#C123456|test-channel> has <https://www.pinterest.com|www.pinterest.com>'
        expected_response = '@U123456 check #test-channel has www.pinterest.com'
        self.assertEqual(expected_response, strip_formatting(test_string))


if __name__ == "__main__":
    unittest.main()
