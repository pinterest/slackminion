from slackminion.dispatcher import MessageDispatcher
from slackminion.slack import SlackEvent, SlackUser, SlackConversation
from slackminion.exceptions import NotSetupError
from slackminion.plugin import PluginManager
from slackminion.webserver import Webserver
from slackminion.utils.async_task import AsyncTaskManager, AsyncTimer
from slackminion.plugins.core import version as my_version
import logging
import datetime
import slack
import asyncio

ignore_subtypes = [
    'bot_message',
    'message_changed',
    'message_replied',
    'message_deleted',
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
        return {}

    async def get_my_conversations(self, *args, **kwargs):
        return await self.api_client.users_conversations(
            exclude_archived='true',
            limit=200,
            types='public_channel,private_channel',
            *args, **kwargs)

    async def update_channels(self):
        self.log.debug('Starting update_channels')
        try:
            resp = await self.get_my_conversations()
            results = resp.get('channels')

            while resp.get('response_metadata').get('next_cursor'):
                cursor = resp.get('response_metadata').get('next_cursor')
                resp = await self.get_my_conversations(cursor=cursor)
                results.extend(resp.get('channels'))
                await asyncio.sleep(1)

            for channel in results:
                self._channels.update(
                    {channel.get('id'): SlackConversation(conversation=channel, api_client=self.api_client)})
        except Exception:  # noqa
            self.log.exception('update_channels failed due to exception')
        self.log.debug(f'Loaded {len(self.channels)} channels.')

    def start(self):
        """Initializes the bot, plugins, and everything."""
        self.log.info(f'Starting SlackMinion version {self.version}')
        self.task_manager = AsyncTaskManager(self)
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

        self._info = await self.api_client.auth_test()

        while self.runnable:
            if first_connect:
                self.log.debug('Starting RTM Client')
                self.task_manager.start_rtm_client(self.rtm_client)
                self.plugins.connect()
                self.task_manager.start_periodic_task(600, self.update_channels)
                first_connect = False
            await self.task_manager.start()
            await asyncio.sleep(1)

    async def stop(self):
        """Does cleanup of bot and plugins."""
        if not self.test_mode:
            self.plugins.save_state()
        self.log.debug('Stopping Task Manager')
        await self.task_manager.shutdown()
        self.log.debug('Stopping RTM client.')

        # cleanup any running timer threads so bot doesn't hang on shutdown
        for t in self.timers:
            t.cancel()
        if self.webserver is not None:
            self.webserver.stop()
        self.plugins.unload_all()

    def send_message(self, channel, text, thread=None, reply_broadcast=None, attachments=None, parse=None,
                     link_names=1):
        """
        Sends a message to the specified channel

        * channel - The channel to send to.  This can be a SlackConversation object, a channel id, or a channel name
        (without the #)
        * text - String to send
        * thread - reply to the thread. See https://api.slack.com/docs/message-threading#threads_party
        * reply_broadcast - Set to true to indicate your reply is germane to all members of a channel
        * parse - Set to "full" for the slack api to linkify names and channels
        """
        if not text:
            self.log.debug('send_message was called without text to send')
            return
        # This doesn't want the # in the channel name
        if isinstance(channel, SlackConversation):
            channel = channel.channel_id
        self.log.debug(f'Trying to send to {channel}: {text[:40]} (truncated)')
        self.api_client.chat_postMessage(
            as_user=True,
            channel=channel,
            text=text,
            thread_ts=thread,
            reply_broadcast=reply_broadcast,
            attachments=attachments,
            parse=parse,
            link_names=link_names,
        )

    def send_im(self, user, text, parse=None):
        """
        Sends a message to a user as an IM

        * user - The user to send to.  This can be a SlackUser object, a user id, or the username (without the @)
        * text - String to send
        """
        if isinstance(user, SlackUser):
            channelid = user.user_id
        else:
            channelid = user
        self.send_message(channelid, text, parse)

    def at_user(self, user, channel_id, text, **kwargs):
        """
        Appends @user Slack formatting to the beginning of a message.

        * user - The SlackUser to send to.
        * channel_id - The channel ID of the channel to send  to
        * text - String to send
        * kwargs - add'l keyword arguments to pass to send_message()
        """
        message = f'{user.at_user}: {text}'
        self.send_message(channel_id, message, **kwargs)

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

        # ignore message subtypes we aren't interested in
        if subtype in ignore_subtypes:
            self.log.info(f"Ignoring message subtype {subtype} from {data.get('user')}")
            self.log.debug(data.get('text'))
            return

        e = SlackEvent(event_type=event_type, **payload)
        self.log.debug("Received event type: %s", e.event_type)

        if e.user_id and e.user_id != self.my_userid:
            if hasattr(self, 'user_manager'):
                e.user = self.user_manager.get(e.user_id)
                if e.user is None:
                    slack_user = SlackUser(user_id=e.user_id, api_client=self.api_client)
                    await slack_user.load()
                    e.user = self.user_manager.set(slack_user)
        if e.channel_id:
            e.channel = await self.get_channel(e.channel_id)
        return e

    def _add_event_handlers(self):
        slack.RTMClient.on(event='channel_joined', callback=self._event_channel_joined)
        slack.RTMClient.on(event='message', callback=self._event_message)
        slack.RTMClient.on(event='error', callback=self._event_error)

    # when the bot is invited to a channel, add the channel to self.channels
    async def _event_channel_joined(self, **payload):
        try:
            self.log.debug(f'Channel joined: {payload}')
            channel_info = payload.get('data').get('channel')
            channel = SlackConversation(conversation=channel_info, api_client=self.api_client)
            self._channels.update({channel.id: channel})
        except Exception:  # noqa
            self.log.exception('Uncaught exception')

    async def _event_message(self, **payload):
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
        self.log.debug(f'Preparing to send  output for  {cmd} with options {cmd_options}')
        if msg.thread_ts:
            thread_ts = msg.thread_ts
        elif cmd_options.get('reply_in_thread'):
            thread_ts = msg.ts
        else:
            thread_ts = None
        parse = cmd_options.get('parse', None)
        if cmd in self.always_send_dm or cmd_options.get('always_send_dm'):
            self.send_im(msg.user, output, parse=parse)
        else:
            self.send_message(msg.channel, output, thread=thread_ts,
                              reply_broadcast=cmd_options.get('reply_broadcast'), parse=parse)

    def _event_error(self, **payload):
        self.log.error(f"Received an error response from Slack: {payload}")

    def get_channel_by_name(self, channel_name):
        channels = [x for x in self.channels.values() if channel_name in x.all_names]
        if len(channels) == 0:
            raise RuntimeError(f'Unable to find channel {channel_name}')
        if len(channels) > 1:
            self.log.warning(f'Found more than one channel named {channel_name}')
        return channels[0]

    async def get_channel(self, channel_id):
        if channel_id in self.channels.keys():
            channel = self.channels.get(channel_id)
        else:
            channel = SlackConversation(None, self.api_client)
            await channel.load(channel_id)
            self._channels.update({channel_id: channel})
        if channel:
            return channel
