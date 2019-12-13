from unittest import mock
from slackminion.slack import SlackIM, SlackChannel, SlackGroup, SlackUser, SlackEvent

test_channel_id = 'C12345678'
test_channel_name = 'testchannel'
test_group_id = 'G12345678'
test_group_name = 'testgroup'
test_user_id = 'U12345678'
test_user_name = 'testuser'
test_user_email = 'root@dev.null'
str_format = '<#{id}|{name}>'
non_existent_user_name = 'doesnotexist'
test_version = '0.0.42'
test_commit = '969d561d'
test_host = 'localhost'
test_port = 80
test_text = "Testing 1..2..3.."
test_user = SlackUser(test_user_id, sc=mock.Mock())
test_command = 'testcmd'
test_output = "some output"
test_thread_ts = "test_thread_ts"

# Channel, result
test_message_data = [
    (SlackIM('D12345678'), 'send_im'),
    (SlackUser(test_user_id, sc=mock.Mock()), 'send_im'),
    (SlackChannel(test_channel_id, sc=mock.Mock()), 'send_message'),
    (SlackGroup(test_group_id, sc=mock.Mock()), 'send_message'),
    ('@testuser', 'send_im'),
    ('#testchannel', 'send_message'),
    ('testchannel', 'send_message'),
    (None, 'send_message'),
]

EXPECTED_PLUGIN_METHODS = [
    'on_connect',
    'on_load',
    'on_unload',
]

test_payload = {
    'data': {
        'user': test_user_id,
        'channel': test_channel_id,
        'text': test_text,
    },
}
