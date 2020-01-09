from builtins import object
import logging
import datetime
import signal
import slack
import asyncio

from slackminion.dispatcher import MessageDispatcher
from slackminion.slack import SlackEvent, SlackUser, SlackRoomIMBase
from slackminion.exceptions import NotSetupError
from slackminion.plugin import PluginManager
from slackminion.webserver import Webserver


class Bot(object):
    rtm_client = None
    web_client = None
    webserver = None
    rtm_client_task = None
    sleep_task = None

    def __init__(self, config, test_mode=False, dev_mode=False):
        self.always_send_dm = []
        self.config = config
        self.dispatcher = MessageDispatcher()
        self.is_setup = False
        self.log = logging.getLogger(type(self).__name__)
        self.plugins = PluginManager(self, test_mode)
        self.runnable = True
        self.sc = None
        self.webserver = None
        self.test_mode = test_mode
        self.reconnect_needed = True
        self.bot_start_time = None
        self.timers = []
        self.event_loop = asyncio.get_event_loop()

        if self.test_mode:
            self.metrics = {
                'startup_time': 0
            }

        from slackminion.plugins.core import version
        self.version = version
        try:
            from slackminion.plugins.core import commit
            self.commit = commit
        except ImportError:
            self.commit = "HEAD"

    def start(self):
        """Initializes the bot, plugins, and everything."""
        self.log.info(f'Starting SlackMinion version {self.version}')
        self.bot_start_time = datetime.datetime.now()
        self.webserver = Webserver(self.config['webserver']['host'], self.config['webserver']['port'])
        self.plugins.load()
        self.plugins.load_state()
        self.rtm_client = slack.RTMClient(token=self.config.get('slack_token'), run_async=True)
        self.web_client = slack.WebClient(token=self.config.get('slack_token'), run_async=True)

        self.always_send_dm = ['_unauthorized_']
        if 'always_send_dm' in self.config:
            self.always_send_dm.extend(['!' + x for x in self.config['always_send_dm']])

        # Rocket is very noisy at debug
        logging.getLogger('Rocket.Errors.ThreadPool').setLevel(logging.INFO)
        self._add_callbacks()
        self.is_setup = True
        if self.test_mode:
            self.metrics['startup_time'] = (datetime.datetime.now() - self.bot_start_time).total_seconds() * 1000.0

    def graceful_shutdown(self):
        self.log.debug('Starting graceful shutdown.')
        self.runnable = False
        self.log.debug('Canceling sleep.')
        self.sleep_task.cancel()
        self.log.debug('Stopping RTM client.')
        self.rtm_client.stop()

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

        try:
            self.rtm_client_task = asyncio.ensure_future(self.rtm_client.start())
            self.event_loop.add_signal_handler(signal.SIGINT, self.graceful_shutdown)
            self.event_loop.add_signal_handler(signal.SIGTERM, self.graceful_shutdown)
            while self.runnable:
                uptime = datetime.datetime.now() - self.bot_start_time
                hours = divmod(uptime.total_seconds(), 3600)[0]
                minutes = divmod(uptime.total_seconds(), 60)[0]
                self.log.info('Slackminion {} running for {} days, {} hours, {} minutes...'.format(
                    self.version,
                    uptime.days,
                    hours,
                    minutes)
                )
                if first_connect:
                    first_connect = False
                    self.plugins.connect()
                self.sleep_task = asyncio.ensure_future(asyncio.sleep(60))
                await self.sleep_task
        except asyncio.exceptions.CancelledError:
            self.log.info('Slack RTM client shutdown by CTRL-C')
        except Exception:
            self.log.exception('Unhandled exception')
            raise

    def stop(self):
        """Does cleanup of bot and plugins."""
        # cleanup any running timer threads so bot doesn't hang on shutdown
        for t in self.timers:
            t.cancel()
        if self.webserver is not None:
            self.webserver.stop()
        if not self.test_mode:
            self.plugins.save_state()
        self.plugins.unload_all()

    async def send_message(self, channel, text, thread=None, reply_broadcast=None, attachments=None):
        """
        Sends a message to the specified channel

        * channel - The channel to send to.  This can be a SlackChannel object, a channel id, or a channel name
        (without the #)
        * text - String to send
        * thread - reply to the thread. See https://api.slack.com/docs/message-threading#threads_party
        * reply_broadcast - Set to true to indicate your reply is germane to all members of a channel
        """
        # This doesn't want the # in the channel name
        if isinstance(channel, SlackRoomIMBase):
            channel = channel.id
        self.log.debug("Trying to send to %s: %s", channel, text)
        await self.web_client.chat_postMessage(as_user=True, channel=channel, text=text, thread=thread,
                                               reply_broadcast=reply_broadcast, attachments=attachments)

    async def send_im(self, user, text):
        """
        Sends a message to a user as an IM

        * user - The user to send to.  This can be a SlackUser object, a user id, or the username (without the @)
        * text - String to send
        """
        if isinstance(user, SlackUser):
            user = user.id
            channelid = self._find_im_channel(user)
        else:
            channelid = user.id
        await self.send_message(channelid, text)

    def _find_im_channel(self, user):
        resp = self.sc.api_call('im.list')
        channels = [x for x in resp['ims'] if x['user'] == user]
        if len(channels) > 0:
            return channels[0]['id']
        resp = self.sc.api_call('im.open', user=user)
        return resp['channel']['id']

    def _load_user_rights(self, user):
        if user is not None:
            if 'bot_admins' in self.config:
                if user.username in self.config['bot_admins']:
                    user.is_admin = True

    def _handle_event(self, event_type, payload):
        self.log.debug(payload)
        data = payload.get('data')
        if 'subtype' in payload.get('data'):
            if payload.get('data').get('subtype') == 'bot_message':
                self.log.info(f"Ignoring bot message from {data.get('username')}")
                self.log.debug(data.get('text'))

        e = SlackEvent(event_type=event_type, sc=self.sc, **payload)
        self.log.debug("Received event type: %s", e.event_type)

        if e.user is not None:
            if hasattr(self, 'user_manager'):
                if not isinstance(e.user, SlackUser):
                    self.log.debug("User is not SlackUser: %s", e.user)
                else:
                    user = self.user_manager.get(e.user.id)
                    if user is None:
                        user = self.user_manager.set(e.user)
                    e.user = user
        return e

    def _add_callbacks(self):
        slack.RTMClient.on(event='message', callback=self._event_message)
        slack.RTMClient.on(event='error', callback=self._event_error)
        slack.RTMClient.on(event='team_migration_started', callback=self._event_error)

    async def _event_message(self, **payload):
        self.log.debug(f"Received message: {payload}")
        msg = self._handle_event('message', payload)

        # The user manager should load rights when a user is added
        if not hasattr(self, 'user_manager'):
            self._load_user_rights(msg.user)
        try:
            cmd, output, cmd_options = await self.dispatcher.push(msg)
        except Exception:
            self.log.exception('Unhandled exception')
            return
        self.log.debug(f"Output from dispatcher: {output}")
        if output:
            await self._prepare_and_send_output(cmd, msg, cmd_options, output)

    async def _prepare_and_send_output(self, cmd, msg, cmd_options, output):
        if cmd_options.get('reply_in_thread'):
            if hasattr(msg, 'thread_ts'):
                thread_ts = msg.thread_ts
            else:
                thread_ts = msg.ts
        else:
            thread_ts = None
        if cmd in self.always_send_dm or cmd_options.get('always_send_dm'):
            await self.send_im(msg.user, output)
        else:
            await self.send_message(msg.channel, output, thread=thread_ts,
                                    reply_broadcast=cmd_options.get('reply_broadcast'))

    def _event_error(self, **payload):
        msg = self._handle_event('error', payload)
        self.log.error("Received an error response from Slack: %s", msg.__dict__)

    def _event_team_migration_started(self, **payload):
        self.log.warning("Slack has initiated a team migration to a new server.  Attempting to reconnect...")
        self.reconnect_needed = True
