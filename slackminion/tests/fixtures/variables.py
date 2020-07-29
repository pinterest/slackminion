from unittest import mock
from slackminion.slack import SlackConversation, SlackUser, SlackEvent
import asyncio


def AsyncMock():
    coro = mock.Mock(name="CoroutineResult")
    corofunc = mock.Mock(name="CoroutineFunction", side_effect=asyncio.coroutine(coro))
    corofunc.coro = coro
    return corofunc


mock_api_client = AsyncMock()
test_channel_id = 'CTESTCHAN'
test_channel_name = 'testchannel'
test_group_id = 'G12345678'
test_group_name = 'testgroup'
test_user_id = 'U12345678'
test_user_name = 'testuser'
test_user_email = 'root@dev.null'
str_format = '<#{id}|{name}>'
non_existent_user_id = 'UABCDEFGH'
test_version = '0.0.42'
test_commit = '969d561d'
test_host = 'localhost'
test_port = 80
test_text = "Testing 1..2..3.."

test_command = 'testcmd'
test_output = "some output"
test_thread_ts = "test_thread_ts"
test_event_type = "test_event_type"

EXPECTED_PLUGIN_METHODS = [
    'on_connect',
    'on_load',
    'on_unload',
]

test_payload = {
    'rtm_client': AsyncMock(),
    'web_client': AsyncMock(),
    'data': {
        'user': test_user_id,
        'channel': test_channel_id,
        'text': test_text,
        'ts': test_thread_ts,
        'thread_ts': test_thread_ts,
        'parse': None
    },
}

test_channel = {
    'name': test_channel_name,
    'id': test_channel_id,
    'is_channel': True,
    'is_im': False
}

test_dm = {
    'name': test_channel_name,
    'id': test_channel_id,
    'is_channel': True,
    'is_im': True
}

test_user_response = {
    'ok': True,
    'user': {
        'id': test_user_id,
        'name': test_user_name,
    }
}

test_user = SlackUser(user_info=test_user_response['user'], api_client=mock.Mock())
test_conversation = SlackConversation(test_channel, api_client=mock.Mock())
