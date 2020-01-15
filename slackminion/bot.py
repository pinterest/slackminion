from slackminion.dispatcher import MessageDispatcher
from slackminion.slack import SlackEvent, SlackUser, SlackConversation
from slackminion.exceptions import NotSetupError
from slackminion.plugin import PluginManager
from slackminion.webserver import Webserver
from slackminion.utils.util import dev_console, output_to_dev_console
from slackminion.utils.async_task import AsyncTaskManager
from slackminion.plugins.core import version as my_version
import logging
import datetime
import slack
import asyncio
import signal


class Bot(object):
    rtm_client = None
    api_client = None
    webserver = None
    _bot_info = None
    _bot_channels = {}
    runnable = True
    always_send_dm = []
    is_setup = False
    bot_start_time = None
    timers = []

    def __init__(self, config, test_mode=False, dev_mode=False):
        self.config = config
        self.dispatcher = MessageDispatcher()
        self.log = logging.getLogger(type(self).__name__)
        self.plugins = PluginManager(self, test_mode)
        self.test_mode = test_mode
        self.dev_mode = dev_mode

        if self.test_mode:
            self.metrics = {
                'startup_time': 0
            }

        self.version = my_version
        try:
            from slackminion.plugins.core import commit
            self.commit = commit
        except ImportError:
            self.commit = "HEAD"

    @property
    def sc(self):
        return self.api_client

    @property
    def channels(self):
        if self.is_setup:
            if self._bot_channels:
                return self._bot_channels
            else:
                self.log.warning('Bot.channels was called but self._bot_channels was empty!')
                return {}
        self.log.warning('Bot.channels was called before bot was setup.')

    async def update_channels(self):
        self.log.debug('Starting update_channels task')
        while True:
            resp = await self.api_client.conversations_list()
            if resp:
                for channel in resp['channels']:
                    self._bot_channels.update({channel.get('id'): SlackConversation(channel, self.api_client)})
            self.log.debug('Completed update_channels task')
            await self.task_manager.sleep(600)

    def start(self):
        """Initializes the bot, plugins, and everything."""
        self.log.info(f'Starting SlackMinion version {self.version}')
        self.task_manager = AsyncTaskManager()
        if not self.dev_mode:
            self.task_manager.create_and_schedule_task(self.update_channels)
        self.task_manager.add_signal_handler(signal.SIGINT, self.graceful_shutdown)
        self.task_manager.add_signal_handler(signal.SIGTERM, self.graceful_shutdown)
        self.bot_start_time = datetime.datetime.now()
        self.webserver = Webserver(self.config['webserver']['host'], self.config['webserver']['port'])
        self.plugins.load()
        self.plugins.load_state()
        if self.dev_mode:
            self.rtm_client = None
        else:
            self.rtm_client = slack.RTMClient(token=self.config.get('slack_token'), run_async=True)
        self.api_client = slack.WebClient(token=self.config.get('slack_token'), run_async=True)

        self.always_send_dm = ['_unauthorized_']
        if 'always_send_dm' in self.config:
            self.always_send_dm.extend(['!' + x for x in self.config['always_send_dm']])

        self._add_event_handlers()
        self.is_setup = True
        if self.test_mode:
            self.metrics['startup_time'] = (datetime.datetime.now() - self.bot_start_time).total_seconds() * 1000.0

    def graceful_shutdown(self):
        self.log.debug('Starting graceful shutdown.')
        self.runnable = False

    async def run(self):
        """
        Connects to slack and enters the main loop.
        """
        # Fail out if setup wasn't run
        if not self.is_setup:
            raise NotSetupError

        # Start the web server
        self.webserver.start()

        first_connect = True

        if not self.dev_mode:
            self.task_manager.create_and_schedule_task(self.rtm_client.start)

        try:
            while self.runnable:
                if first_connect:
                    self.plugins.connect()
                    first_connect = False

                if self.dev_mode:
                    try:
                        await dev_console(self)
                    except EOFError:
                        self.runnable = False
                await self.task_manager.sleep(60)
        except asyncio.exceptions.CancelledError:
            self.log.info('Bot shutdown has been triggered by CTRL-C')
        except Exception:
            self.log.exception('Unhandled exception')

    def stop(self):
        """Does cleanup of bot and plugins."""
        if hasattr(self, 'task_manager'):
            self.task_manager.shutdown()
        if not self.dev_mode:
            self.log.debug('Stopping RTM client.')
            self.rtm_client.stop()
        # cleanup any running timer threads so bot doesn't hang on shutdown
        for t in self.timers:
            t.cancel()
        if self.webserver is not None:
            self.webserver.stop()
        if not self.test_mode:
            self.plugins.save_state()
        self.plugins.unload_all()

    def send_message(self, channel, text, thread=None, reply_broadcast=None, attachments=None):
        """
        Sends a message to the specified channel

        * channel - The channel to send to.  This can be a SlackChannel object, a channel id, or a channel name
        (without the #)
        * text - String to send
        * thread - reply to the thread. See https://api.slack.com/docs/message-threading#threads_party
        * reply_broadcast - Set to true to indicate your reply is germane to all members of a channel
        """
        if not text:
            self.log.debug('send_message was called without text to send')
            return
        # This doesn't want the # in the channel name
        if isinstance(channel, SlackConversation):
            channel = channel.id
        self.log.debug(f'Trying to send to {channel}: {text[:40]} (truncated)')
        if self.dev_mode:
            output_to_dev_console(text)
        else:
            self.task_manager.create_and_schedule_task(
                self.api_client.chat_postMessage, as_user=True, channel=channel, text=text, thread=thread,
                reply_broadcast=reply_broadcast, attachments=attachments)

    def send_im(self, user, text):
        """
        Sends a message to a user as an IM

        * user - The user to send to.  This can be a SlackUser object, a user id, or the username (without the @)
        * text - String to send
        """
        if self.dev_mode:
            output_to_dev_console(text)
            return
        if isinstance(user, SlackUser):
            user = user.user_id
            channelid = self._find_im_channel(user)
        else:
            channelid = user.id

        self.send_message(channelid, text)

    def _load_user_rights(self, user):
        if user is not None:
            if 'bot_admins' in self.config:
                if user.username in self.config['bot_admins']:
                    user.set_admin(True)

    def _handle_event(self, event_type, payload):
        self.log.debug(payload)
        data = payload.get('data')
        if 'subtype' in payload.get('data'):
            if payload.get('data').get('subtype') == 'bot_message':
                self.log.info(f"Ignoring bot message from {data.get('username')}")
                self.log.debug(data.get('text'))
                return

        e = SlackEvent(event_type=event_type, **payload)
        self.log.debug("Received event type: %s", e.event_type)

        if e.user_id:
            if hasattr(self, 'user_manager'):
                e.user = self.user_manager.get(e.user_id)
                if e.user is None:
                    e.user = self.user_manager.set(e.user)
        return e

    def _add_event_handlers(self):
        slack.RTMClient.on(event='message', callback=self._event_message)
        slack.RTMClient.on(event='error', callback=self._event_error)

    async def _event_message(self, **payload):
        self.log.debug(f"Received message: {payload}")
        msg = self._handle_event('message', payload)

        # The user manager should load rights when a user is added
        if not hasattr(self, 'user_manager'):
            self._load_user_rights(msg.user)
        try:
            cmd, output, cmd_options = await self.dispatcher.push(msg)
            self.log.debug(f"Output from dispatcher: {output}")

            if output:
                self._prepare_and_send_output(cmd, msg, cmd_options, output)
        except Exception:
            self.log.exception('Unhandled exception')
            return

    def _prepare_and_send_output(self, cmd, msg, cmd_options, output):
        if cmd_options.get('reply_in_thread'):
            if hasattr(msg, 'thread_ts'):
                thread_ts = msg.thread_ts
            else:
                thread_ts = msg.ts
        else:
            thread_ts = None
        if cmd in self.always_send_dm or cmd_options.get('always_send_dm'):
            self.send_im(msg.user, output)
        else:
            self.send_message(msg.channel, output, thread=thread_ts,
                              reply_broadcast=cmd_options.get('reply_broadcast'))

    def _event_error(self, **payload):
        msg = self._handle_event('error', payload)
        self.log.error("Received an error response from Slack: %s", msg.__dict__)

    def get_channel(self, channel_id):
        if channel_id in self.channels.keys():
            channel = self.channels.get(channel_id)
        else:
            channel = SlackConversation(None, self.api_client)
            channel.load(channel_id)
        return channel
