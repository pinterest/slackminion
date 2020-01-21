from slackminion.dispatcher import MessageDispatcher
from slackminion.slack import SlackEvent, SlackUser, SlackConversation
from slackminion.exceptions import NotSetupError
from slackminion.plugin import PluginManager
from slackminion.webserver import Webserver
from slackminion.utils.util import dev_console, output_to_dev_console
from slackminion.utils.async_task import AsyncTaskManager, AsyncTimer
from slackminion.plugins.core import version as my_version
import logging
import datetime
import slack
import asyncio
import signal

ignore_subtypes = [
    'bot_message',
    'message_changed',
]


class Bot(object):
    rtm_client = None
    api_client = None
    webserver = None
    _info = {}
    _channels = {}
    runnable = True
    shutting_down = False
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
        self.event_loop = asyncio.get_event_loop()

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
    def my_username(self):
        return self._info.get('name')

    @property
    def my_userid(self):
        return self._info.get('user_id')

    @property
    def channels(self):
        if self.is_setup:
            if self._channels:
                return self._channels
            else:
                self.log.warning('Bot.channels was called but self._bot_channels was empty!')
                return {}
        self.log.warning('Bot.channels was called before bot was setup.')

    async def update_channels(self):
        self.log.debug('Starting update_channels')
        resp = await self.api_client.conversations_list()
        if resp:
            for channel in resp['channels']:
                self._channels.update({channel.get('id'): SlackConversation(channel, self.api_client)})
        self.log.debug('Completed update_channels task')

    def start(self):
        """Initializes the bot, plugins, and everything."""
        self.log.info(f'Starting SlackMinion version {self.version}')
        self.task_manager = AsyncTaskManager()
        self.bot_start_time = datetime.datetime.now()

        self.log.debug('Slack clients initialized.')
        self.webserver = Webserver(self.config['webserver']['host'], self.config['webserver']['port'])

        self.plugins.load()
        self.plugins.load_state()

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
        if not self.shutting_down:
            self.shutting_down = True
            self.log.debug('Starting graceful shutdown.')
            self.task_manager.runnable = False
            self.runnable = False

    async def run(self):
        """
        Connects to slack and enters the main loop.
        """
        # Fail out if setup wasn't run
        if not self.is_setup:
            raise NotSetupError

        # Start the web server
        self.log.debug('Starting Web Server')
        self.webserver.start()
        first_connect = True
        self.log.debug('Starting RTM Client')
        self.rtm_client.start()
        self.event_loop.add_signal_handler(signal.SIGINT, self.graceful_shutdown)
        self.event_loop.add_signal_handler(signal.SIGTERM, self.graceful_shutdown)
        self._info = await self.api_client.auth_test()

        while self.runnable:
            if first_connect:
                self.plugins.connect()
                await self.task_manager.start_periodic_task(600, self.update_channels)
                first_connect = False
            await self.task_manager.start()

    async def stop(self):
        """Does cleanup of bot and plugins."""
        self.log.debug('Stopping Task Manager')
        await self.task_manager.shutdown()
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

        * channel - The channel to send to.  This can be a SlackConversation object, a channel id, or a channel name
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
            channelid = user.user_id
        else:
            channelid = user

        self.send_message(channelid, text)

    def _load_user_rights(self, user):
        self.log.debug(f'Loading user rights for {user}')
        if user is not None:
            if 'bot_admins' in self.config:
                if user.username in self.config['bot_admins']:
                    user.set_admin(True)

    async def _handle_event(self, event_type, payload):
        self.log.debug(payload)
        data = payload.get('data')
        subtype = payload.get('data').get('subtype')
        if subtype in ignore_subtypes:
            self.log.info(f"Ignoring message subtype {subtype} from {data.get('username')}")
            self.log.debug(data.get('text'))
            return

        e = SlackEvent(event_type=event_type, **payload)
        self.log.debug("Received event type: %s", e.event_type)

        if e.user_id:
            if hasattr(self, 'user_manager'):
                e.user = self.user_manager.get(e.user_id)
                if e.user is None:
                    slack_user = SlackUser(user_id=e.user_id, api_client=self.api_client)
                    await slack_user.load()
                    e.user = self.user_manager.set(slack_user)
        return e

    def _add_event_handlers(self):
        slack.RTMClient.on(event='message', callback=self._event_message)
        slack.RTMClient.on(event='error', callback=self._event_error)

    async def _event_message(self, **payload):
        self.log.debug(f"Received message: {payload}")
        msg = await self._handle_event('message', payload)
        if not msg:
            return

        # The user manager should load rights when a user is added
        if not hasattr(self, 'user_manager'):
            self._load_user_rights(msg.user)
        try:
            self.log.debug(f'Sending to dispatcher: {msg}')
            cmd, output, cmd_options = await self.dispatcher.push(msg, self.dev_mode)
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

    def get_channel_by_name(self, channel_name):
        channels = [x for x in self.channels.values() if x.name == channel_name]
        if len(channels) == 0:
            return
        if len(channels) > 1:
            self.log.warning(f'Found more than one channel named {channel_name}')
        return self.get_channel(channels[0].id)

    def get_channel(self, channel_id):
        if channel_id in self.channels.keys():
            channel = self.channels.get(channel_id)
        else:
            channel = SlackConversation(None, self.api_client)
            channel.load(channel_id)
        if channel:
            return channel
