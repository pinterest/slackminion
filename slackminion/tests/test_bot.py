import yaml

from slackminion.bot import Bot
from slackminion.dispatcher import MessageDispatcher
from slackminion.exceptions import NotSetupError
from slackminion.plugins.core import version
from slackminion.tests.fixtures import *


class TestBot(unittest.TestCase):
    def setUp(self):
        with open('config.yaml.example', 'r') as f:
            self.object = Bot(config=yaml.safe_load(f), test_mode=True)
        self.test_event = SlackEvent(event_type='tests', sc=self.object.sc, **test_payload)

    def tearDown(self):
        self.object = None

    def test_init(self):
        assert self.object.version == version
        assert self.object.commit == 'HEAD'

    def test_start(self):
        self.object.start()
        assert self.object.is_setup is True

    def test_stop(self):
        self.object.stop()

    async def test_run_without_start(self):
        with self.assertRaises(NotSetupError) as e:
            await self.object.run()
        assert 'Bot not setup' in str(e)

    @mock.patch('slackminion.bot.slack.RTMClient.on')
    def test_add_callbacks(self, mock_rtmclient_on):
        self.object._add_callbacks()
        self.assertEqual(mock_rtmclient_on.call_count, 3)

    async def test_event_message_no_user_manager(self):
        # mock out the methods we don't want to actually call
        self.object._handle_event = mock.Mock(return_value=self.test_event)
        self.object.dispatcher = mock.Mock()
        self.object.dispatcher.push.return_value = (test_command, test_output, None)
        self.object._prepare_and_send_output = mock.Mock()
        self.object._load_user_rights = mock.Mock()

        # for this test, bot has no user manager
        self.object.user_manager = None

        await self.object._event_message(**test_payload)
        self.object._handle_event.assert_called_with('message', test_payload)
        self.object._load_user_rights.assert_not_called()
        self.object.dispatcher.push.assert_called_with(self.test_event)
        self.object.log.debug.assert_called_with(f'Output from dispatcher: {test_output}')
        self.object._prepare_and_send_output.assert_called_with(test_command, self.test_event, None, test_output)

    async def test_event_message_with_user_manager(self):
        # mock out the methods we don't want to actually call
        self.object._handle_event = mock.Mock(return_value=self.test_event)
        self.object.dispatcher = mock.Mock()
        self.object.dispatcher.push.return_value = (test_command, test_output, None)
        self.object._prepare_and_send_output = mock.Mock()
        self.object._load_user_rights = mock.Mock()

        # for this test, bot has a user manager
        self.object.user_manager = mock.Mock()

        await self.object._event_message(**test_payload)
        self.object.user_manager.get.assert_called_with(test_user_id)
        self.object._handle_event.assert_called_with('message', test_payload)
        self.object._load_user_rights.assert_not_called()
        self.object.dispatcher.push.assert_called_with(self.test_event)
        self.object.log.debug.assert_called_with(f'Output from dispatcher: {test_output}')
        self.object._prepare_and_send_output.assert_called_with(test_command, self.test_event, None, test_output)

    # test reloading user if user is None
    async def test_event_message_with_user_manager_but_no_user(self):
        # mock out the methods we don't want to actually call
        self.object._handle_event = mock.Mock(return_value=self.test_event)
        self.object.dispatcher = mock.Mock()
        self.object.dispatcher.push.return_value = (test_command, test_output, None)
        self.object._prepare_and_send_output = mock.Mock()
        self.object._load_user_rights = mock.Mock()

        # for this test, bot has a user manager but .get() returns None
        # so the bot has to to look up user again using .set()
        self.object.user_manager = mock.Mock()
        self.object.user_manager.get.return_value = None
        self.object.user_manager.set.return_value = TestUser

        await self.object._event_message(**test_payload)
        self.object.user_manager.get.assert_called_with(test_user_id)
        self.object._handle_event.assert_called_with('message', test_payload)
        self.object._load_user_rights.assert_not_called()
        self.object.dispatcher.push.assert_called_with(self.test_event)
        self.object.log.debug.assert_called_with(f'Output from dispatcher: {test_output}')
        self.object._prepare_and_send_output.assert_called_with(test_command, self.test_event, None, test_output)

    # test _prepare_and_send_output without any command options set (reply in thread, etc.)
    async def test_prepare_and_send_output_no_cmd_options(self):
        self.object._send_message = mock.Mock()
        self.object._send_im = mock.Mock()
        #    async def _prepare_and_send_output(self, cmd, msg, cmd_options, output):
        self.object._prepare_and_send_output(test_command, self.test_event, {}, test_output)
        self.object._send_message.assert_called_with(test_channel_id, test_output, thread=None, reply_broadcast=False)

    # test _prepare_and_send_output with various options
    async def test_prepare_and_send_output_no_cmd_options(self):
        self.object._send_message = mock.Mock()
        self.object._send_im = mock.Mock()
        #    async def _prepare_and_send_output(self, cmd, msg, cmd_options, output):
        cmd_options = {
            'reply_in_thread': True
        }
        self.test_event.thread_ts = test_thread_ts
        self.object._prepare_and_send_output(test_command, self.test_event, cmd_options, test_output)
        self.object._send_message.assert_called_with(test_channel_id, test_output, thread=test_thread_ts,
                                                     reply_broadcast=False)

        cmd_options = {
            'reply_in_thread': True,
            'reply_broadcast': True,
        }

        self.object._prepare_and_send_output(test_command, self.test_event, cmd_options, test_output)
        self.object._send_message.assert_called_with(test_channel_id, test_output, thread=test_thread_ts,
                                                     reply_broadcast=True)

    def test_event_error(self):
        self.object._handle_event = mock.Mock()
        self.object._event_error(**test_payload)
        self.object._handle_event.assert_called_with('error', test_payload)

    def test_event_team_migration_started(self):
        self.object._handle_event = mock.Mock()
        self.object.log = mock.Mock()
        self.object.reconnect_needed = False
        self.object._event_team_migration_started(**test_payload)
        self.object._handle_event.assert_not_called()
        self.object.log.warning.assert_called_with(
            "Slack has initiated a team migration to a new server.  Attempting to reconnect...")
        self.assertEqual(self.object.reconnect_needed, True)