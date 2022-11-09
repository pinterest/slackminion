from copy import deepcopy

import yaml

from slackminion.bot import Bot
from slackminion.exceptions import NotSetupError
from slackminion.plugins.core import version
from slackminion.tests.fixtures import *


class PluginWithEvents(BasePlugin):
    notify_event_types = [test_event_type]

    def handle_event(self):
        pass


class TestBot(unittest.TestCase):
    @mock.patch("slackminion.slack.SlackUser")
    def setUp(self, mock_user):
        with open("config.yaml.example", "r") as f:
            self.object = Bot(config=yaml.safe_load(f), test_mode=True)
        self.test_event = SlackEvent(event_type="tests", **test_payload)
        self.object.rtm_client = AsyncMock()
        self.object.api_client = AsyncMock()
        self.object.log = mock.Mock()
        self.test_payload = deepcopy(test_payload)

    def tearDown(self):
        self.object = None

    def test_init(self):
        assert self.object.version == version
        assert self.object.commit == "HEAD"

    @mock.patch("slackminion.bot.AsyncTaskManager")
    @mock.patch("slackminion.bot.AsyncWebClient")
    def test_start(self, mock_slack, mock_async):
        self.object.start()
        assert self.object.is_setup is True

    @async_test
    async def test_stop(self):
        self.object.task_manager = mock.Mock()
        self.object.task_manager.shutdown = AsyncMock()
        self.object.task_manager.shutdown.coro.return_value = None
        await self.object.stop()
        self.object.task_manager.shutdown.assert_called()

    @async_test
    async def test_run_without_start(self):
        with self.assertRaises(NotSetupError) as e:
            await self.object.run()
            assert "Bot not setup" in str(e)

    @mock.patch("slackminion.bot.MyRTMClient")
    def test_add_callbacks(self, mock_rtm):
        self.object._add_event_handlers()
        self.assertEqual(mock_rtm.on.call_count, 3)

    @async_test
    async def test_event_message_no_user_manager(self):
        # mock out the methods we don't want to actually call
        self.object._parse_event = AsyncMock()
        self.object._parse_event.coro.return_value = self.test_event
        self.object.dispatcher = mock.Mock()
        self.object.dispatcher.push = AsyncMock()
        self.object.dispatcher.push.coro.return_value = (
            test_command,
            test_output,
            None,
        )
        self.object.dispatcher.push.coro.return_value = (
            test_command,
            test_output,
            None,
        )
        self.object._prepare_and_send_output = AsyncMock()
        self.object._load_user_rights = mock.Mock()

        # for this test, bot has no user manager
        self.object.user_manager = None

        await self.object._event_message(**test_payload)
        self.object._parse_event.assert_called_with(test_payload)
        self.object._load_user_rights.assert_not_called()
        self.object.dispatcher.push.assert_called_with(self.test_event, False)
        self.object.log.info.assert_called_with(
            f"Output from dispatcher: {test_output}"
        )
        self.object._prepare_and_send_output.assert_called_with(
            test_command, self.test_event, None, test_output
        )

    @async_test
    async def test_event_message_with_user_manager(self):
        # mock out the methods we don't want to actually call
        self.object._parse_event = AsyncMock()
        self.object._parse_event.coro.return_value = self.test_event
        self.object.dispatcher = mock.Mock()
        self.object.dispatcher.push = AsyncMock()
        self.object.dispatcher.push.coro.return_value = (
            test_command,
            test_output,
            None,
        )
        self.object._prepare_and_send_output = AsyncMock()
        self.object._load_user_rights = mock.Mock()
        self.object.log = mock.Mock()

        # for this test, bot has a user manager
        self.object.user_manager = mock.Mock()

        await self.object._event_message(**test_payload)
        self.object._parse_event.assert_called_with(test_payload)
        self.object._load_user_rights.assert_not_called()
        self.object.dispatcher.push.assert_called_with(self.test_event, False)
        self.object.log.info.assert_called_with(
            f"Output from dispatcher: {test_output}"
        )
        self.object._prepare_and_send_output.assert_called_with(
            test_command, self.test_event, None, test_output
        )

    # test reloading user if user is None
    @async_test
    async def test_event_message_with_manager_reload(self):
        self.test_payload["data"].update()
        # mock out the methods we don't want to actually call
        self.object._parse_event = AsyncMock()
        self.test_event.user = mock.Mock()
        self.object._parse_event.coro.return_value = self.test_event
        self.object.dispatcher = mock.Mock()
        self.object.dispatcher.push = AsyncMock()
        self.object.log = mock.Mock()
        self.object.dispatcher.push.coro.return_value = (
            test_command,
            test_output,
            None,
        )
        self.object._prepare_and_send_output = mock.Mock()
        self.object._load_user_rights = mock.Mock()
        self.object.user_manager = None
        delattr(self.object, "user_manager")

        await self.object._event_message(**test_payload)

        self.object._parse_event.assert_called_with(test_payload)
        self.object.dispatcher.push.assert_called_with(self.test_event, False)
        self.object.log.info.assert_called_with(
            f"Output from dispatcher: {test_output}"
        )
        self.object._prepare_and_send_output.assert_called_with(
            test_command, self.test_event, None, test_output
        )

    @async_test
    async def test_event_message_with_user_manager_but_no_user(self):
        # mock out the methods we don't want to actually call
        self.object._parse_event = AsyncMock()
        self.object._parse_event.coro.return_value = self.test_event
        self.object.dispatcher = mock.Mock()
        self.object.dispatcher.push = AsyncMock()
        self.object.log = mock.Mock()
        self.object.dispatcher.push.coro.return_value = (
            test_command,
            test_output,
            None,
        )
        self.object._prepare_and_send_output = AsyncMock()
        self.object._load_user_rights = mock.Mock()
        self.object.user_manager = mock.Mock()

        await self.object._event_message(**test_payload)

        self.object._parse_event.assert_called_with(test_payload)
        self.object._load_user_rights.assert_not_called()
        self.object.dispatcher.push.assert_called_with(self.test_event, False)
        self.object.log.info.assert_called_with(
            f"Output from dispatcher: {test_output}"
        )
        self.object._prepare_and_send_output.assert_called_with(
            test_command, self.test_event, None, test_output
        )

    @async_test
    async def test_parse_event_uncached_user(self):
        self.object.log = mock.Mock()
        # for this test, bot has a user manager but .get() returns None
        # so the bot has to to look up user again using .set()
        self.object.user_manager = mock.Mock()
        self.object.user_manager.get.return_value = None
        self.object.user_manager.set.return_value = test_user
        self.object.get_channel = AsyncMock()
        self.object.api_client.users_info = AsyncMock()
        self.object.api_client.users_info.coro.return_value = test_user_response
        await self.object._parse_event(test_payload)
        self.object.user_manager.get.assert_called_with(test_user_id)
        self.object.user_manager.set.assert_called()

    # test _prepare_and_send_output without any command options set (reply in thread, etc.)
    @async_test
    async def test_prepare_and_send_output_no_cmd_options(self):
        self.object.send_message = AsyncMock()
        self.object.send_im = mock.Mock()
        self.object.web_client = AsyncMock()
        #    async def _prepare_and_send_output(self, cmd, msg, cmd_options, output):
        await self.object._prepare_and_send_output(
            test_command, self.test_event, {}, test_output
        )
        self.object.send_message.assert_called_with(
            self.test_event.channel,
            test_output,
            thread=test_thread_ts,
            reply_broadcast=None,
            parse=None,
        )

    # test _prepare_and_send_output with various options
    @async_test
    async def test_prepare_and_send_output_with_cmd_options(self):
        self.object.send_message = AsyncMock()
        self.object.send_im = mock.Mock()
        self.object.web_client = AsyncMock()
        cmd_options = {"reply_in_thread": True}
        self.assertEqual(self.test_event.thread_ts, test_thread_ts)
        await self.object._prepare_and_send_output(
            test_command, self.test_event, cmd_options, test_output
        )
        self.object.send_message.assert_called_with(
            self.test_event.channel,
            test_output,
            thread=test_thread_ts,
            reply_broadcast=None,
            parse=None,
        )

        cmd_options = {
            "reply_in_thread": True,
            "reply_broadcast": True,
        }

        await self.object._prepare_and_send_output(
            test_command, self.test_event, cmd_options, test_output
        )
        self.object.send_message.assert_called_with(
            self.test_event.channel,
            test_output,
            thread=test_thread_ts,
            reply_broadcast=True,
            parse=None,
        )

        cmd_options = {"parse": "full"}

        await self.object._prepare_and_send_output(
            test_command, self.test_event, cmd_options, test_output
        )
        self.object.send_message.assert_called_with(
            self.test_event.channel,
            test_output,
            thread=test_thread_ts,
            reply_broadcast=None,
            parse="full",
        )

        cmd_options = {}

        await self.object._prepare_and_send_output(
            test_command, self.test_event, cmd_options, test_output
        )
        self.object.send_message.assert_called_with(
            self.test_event.channel,
            test_output,
            thread=test_thread_ts,
            reply_broadcast=None,
            parse=None,
        )

    @async_test
    async def test_event_error(self):
        await self.object._event_error(**test_payload)
        self.object.log.error.assert_called_with(
            f"Received an error response from Slack: {test_payload}"
        )

    def test_get_channel_by_name(self):
        self.object.is_setup = True
        self.object._channels = {test_channel_name: test_conversation}
        self.assertEqual(
            self.object.get_channel_by_name(test_channel_name), test_conversation
        )

    def test_get_channel_by_name_bot_not_setup(self):
        self.object.is_setup = False
        self.object._channels = {test_channel_name: TestChannel}
        with self.assertRaises(RuntimeError):
            self.object.get_channel_by_name(test_channel_name)
        self.object.log.warning.assert_called_with(
            "Bot.channels was called before bot was setup."
        )

    def test_get_channel_by_name_bot_no_channels(self):
        self.object.is_setup = True
        self.object._channels = {}
        with self.assertRaises(RuntimeError):
            self.object.get_channel_by_name(test_channel_name)
        self.object.log.warning.assert_called_with(
            "Bot.channels was called but self._bot_channels was empty!"
        )

    @async_test
    async def test_at_user(self):
        self.object.send_message = AsyncMock()
        test_message = "hi"
        expected_message = f"{test_user.at_user}: {test_message}"
        await self.object.at_user(test_user, test_channel_id, test_message)
        self.object.send_message.assert_called_with(test_channel_id, expected_message)

    def test_unpack_payload(self):
        event_type, data = self.object._unpack_payload(**test_payload)
        self.assertEqual(event_type, test_payload["data"]["type"])
        self.assertEqual(data, test_payload["data"])

    @mock.patch("slackminion.bot.MyRTMClient")
    @async_test
    async def test_handle_plugin_event(self, mock_rtm):
        self.object.plugin_manager = mock.Mock()
        plugin = PluginWithEvents(self.object)
        plugin.handle_event = mock.Mock()
        self.object.plugin_manager.broadcast_event = AsyncMock()
        self.object.plugin_manager.plugins = [plugin]
        self.object._add_event_handlers()
        self.assertEqual(mock_rtm.on.call_count, 4)
        mock_rtm.on.assert_called_with(
            event=test_event_type, callback=self.object._event_plugin
        )
        await self.object._event_plugin(**test_payload)
        self.object.plugin_manager.broadcast_event.assert_called_with(
            test_event_type, test_payload["data"]
        )


if __name__ == "__main__":
    unittest.main()
