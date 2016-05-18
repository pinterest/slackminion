import logging
from datetime import datetime
from time import sleep

from slackminion.dispatcher import MessageDispatcher
from slackminion.slack import SlackEvent, SlackUser, SlackRoomIMBase, ThreadedSlackClient
from slackminion.exceptions import NotSetupError
from slackminion.plugin import PluginManager
from slackminion.webserver import Webserver


def eventhandler(*args, **kwargs):
    """
    Decorator.  Marks a function as a receiver for the specified slack event(s).

    * events - String or list of events to handle
    """
    def wrapper(func):
        if isinstance(kwargs['events'], basestring):
            kwargs['events'] = [kwargs['events']]
        func.is_eventhandler = True
        func.events = kwargs['events']
        return func
    return wrapper


class Bot(object):
    def __init__(self, config, test_mode=False):
        self.always_send_dm = []
        self.config = config
        self.dispatcher = MessageDispatcher()
        self.event_handlers = {}
        self.is_setup = False
        self.log = logging.getLogger(type(self).__name__)
        self.plugins = PluginManager(self, test_mode)
        self.runnable = True
        self.sc = None
        self.webserver = None
        self.test_mode = test_mode
        self.reconnect_needed = True

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
        if self.test_mode:
            bot_start_time = datetime.now()
        self.plugins.load()
        self.plugins.load_state()
        self._find_event_handlers()
        self.sc = ThreadedSlackClient(self.config['slack_token'])
        self.webserver = Webserver(self.config['webserver']['host'], self.config['webserver']['port'])

        self.always_send_dm = ['_unauthorized_']
        if 'always_send_dm' in self.config:
            self.always_send_dm.extend(map(lambda x: '!' + x, self.config['always_send_dm']))

        # Rocket is very noisy at debug
        logging.getLogger('Rocket.Errors.ThreadPool').setLevel(logging.INFO)

        self.is_setup = True
        if self.test_mode:
            self.metrics['startup_time'] = (datetime.now() - bot_start_time).total_seconds() * 1000.0

    def _find_event_handlers(self):
        for name in dir(self):
            method = getattr(self, name)
            if callable(method) and hasattr(method, 'is_eventhandler'):
                for event in method.events:
                    self.event_handlers[event] = method

    def run(self):
        """Connects to slack and enters the main loop."""
        # Fail out if setup wasn't run
        if not self.is_setup:
            raise NotSetupError

        # Start the web server
        self.webserver.start()

        first_connect = True

        try:
            while self.runnable:
                if self.reconnect_needed:
                    if not self.sc.rtm_connect():
                        return False
                    self.reconnect_needed = False
                    if first_connect:
                        first_connect = False
                        self.plugins.connect()

                # Get all waiting events - this always returns a list
                try:
                    events = self.sc.rtm_read()
                except AttributeError:
                    self.log.exception('Something has failed in the slack rtm library.  This is fatal.')
                    self.runnable = False
                    events = []
                except:
                    self.log.exception('Unhandled exception in rtm_read()')
                    self.reconnect_needed = True
                    events = []
                for e in events:
                    try:
                        self._handle_event(e)
                    except KeyboardInterrupt:
                        # Gracefully shutdown
                        self.runnable = False
                    except:
                        self.log.exception('Unhandled exception in event handler')
                sleep(0.1)
        except KeyboardInterrupt:
            # On ctrl-c, just exit
            pass
        except:
            self.log.exception('Unhandled exception')

    def stop(self):
        """Does cleanup of bot and plugins."""
        if self.webserver is not None:
            self.webserver.stop()
        if not self.test_mode:
            self.plugins.save_state()

    def send_message(self, channel, text):
        """
        Sends a message to the specified channel

        * channel - The channel to send to.  This can be a SlackChannel object, a channel id, or a channel name (without the #)
        * text - String to send
        """
        # This doesn't want the # in the channel name
        if isinstance(channel, SlackRoomIMBase):
            channel = channel.id
        self.log.debug("Trying to send to %s: %s", channel, text)
        self.sc.rtm_send_message(channel, text)

    def send_im(self, user, text):
        """
        Sends a message to a user as an IM

        * user - The user to send to.  This can be a SlackUser object, a user id, or the username (without the @)
        * text - String to send
        """
        if isinstance(user, SlackUser):
            user = user.id
        channelid = self._find_im_channel(user)
        self.send_message(channelid, text)

    def _find_im_channel(self, user):
        resp = self.sc.api_call('im.list')
        channels = filter(lambda x: x['user'] == user, resp['ims'])
        if len(channels) > 0:
            return channels[0]['id']
        resp = self.sc.api_call('im.open', user=user)
        return resp['channel']['id']

    def _load_user_rights(self, user):
        if user is not None:
            if 'bot_admins' in self.config:
                if user.username in self.config['bot_admins']:
                    user.is_admin = True

    def _handle_event(self, event):
        if 'type' not in event:
            # This is likely a notification that the bot was mentioned
            self.log.debug("Received odd event: %s", event)
            return
        e = SlackEvent(sc=self.sc, **event)
        self.log.debug("Received event type: %s", e.type)

        if e.user is not None:
            if hasattr(self, 'user_manager'):
                if not isinstance(e.user, SlackUser):
                    self.log.debug("User is not SlackUser: %s", e.user)
                else:
                    user = self.user_manager.get(e.user.id)
                    if user is None:
                        user = self.user_manager.set(e.user)
                    e.user = user

        if e.type in self.event_handlers:
            self.event_handlers[e.type](e)

    @eventhandler(events='message')
    def _event_message(self, msg):
        self.log.debug("Message.message: %s: %s: %s", msg.channel, msg.user, msg.__dict__)

        # The user manager should load rights when a user is added
        if not hasattr(self, 'user_manager'):
            self._load_user_rights(msg.user)
        try:
            cmd, output = self.dispatcher.push(msg)
        except:
            self.log.exception('Unhandled exception')
            return
        self.log.debug("Output from dispatcher: %s", output)
        if output:
            if cmd in self.always_send_dm:
                self.send_im(msg.user, output)
            else:
                self.send_message(msg.channel, output)

    @eventhandler(events='error')
    def _event_error(self, msg):
        self.log.error("Received an error response from Slack: %s", msg.__dict__)

    @eventhandler(events='team_migration_started')
    def _event_team_migration_started(self, msg):
        self.log.warn("Slack has initiated a team migration to a new server.  Attempting to reconnect...")
        self.reconnect_needed = True
