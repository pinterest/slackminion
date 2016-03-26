import logging

from slackclient import SlackClient
from time import sleep

from dispatcher import MessageDispatcher
from slack import SlackEvent, SlackChannel, SlackUser
from webserver import Webserver


class NotSetupError(Exception):
    def __str__(self):
        return "Bot not setup.  Please run start() before run()."


def eventhandler(*args, **kwargs):
    def wrapper(func):
        if isinstance(kwargs['events'], basestring):
            kwargs['events'] = [kwargs['events']]
        func.is_eventhandler = True
        func.events = kwargs['events']
        return func
    return wrapper


class Bot(object):
    def __init__(self, config):
        self.config = config
        self.sc = None
        self.log = logging.getLogger(__name__)
        self.dispatcher = MessageDispatcher()
        self.event_handlers = {}
        self.webserver = None
        self.is_setup = False
        self.runnable = True
        self.always_send_dm = []

    def start(self):
        self._load_plugins()
        self._find_event_handlers()
        self.sc = SlackClient(self.config['slack_token'])
        self.webserver = Webserver(self.config['webserver']['host'], self.config['webserver']['port'])

        self.always_send_dm = ['_unauthorized_']
        if 'always_send_dm' in self.config:
            self.always_send_dm.extend(map(lambda x: '!' + x, self.config['always_send_dm']))

        # Rocket is very noisy at debug
        logging.getLogger('Rocket.Errors.ThreadPool').setLevel(logging.INFO)

        self.is_setup = True

    def _load_plugins(self):
        import os
        import sys

        # Add plugin dir for extra plugins
        sys.path.append(os.path.join(os.getcwd(), self.config['plugin_dir']))
        if 'plugins' not in self.config:
            self.config['plugins'] = []

        # Add core plugins
        self.config['plugins'].insert(0, 'slackminion.plugins.core.Core')

        for plugin_name in self.config['plugins']:
            # module_path.plugin_class_name
            module, name = plugin_name.rsplit('.', 1)
            try:
                plugin = __import__(module, fromlist=['']).__dict__[name]
            except ImportError:
                self.log.exception("Failed to load plugin %s", name)

            # load plugin config if available
            config = {}
            if name in self.config['plugin_settings']:
                config = self.config['plugin_settings'][name]
            try:
                self.dispatcher.register_plugin(plugin(self, config=config))
            except:
                self.log.exception("Failed to register plugin %s", name)

    def _find_event_handlers(self):
        for name, method in self.__class__.__dict__.iteritems():
            if hasattr(method, 'is_eventhandler'):
                for event in method.events:
                    self.event_handlers[event] = method

    def run(self):

        # Fail out if setup wasn't run
        if not self.is_setup:
            raise NotSetupError

        if not self.sc.rtm_connect():
            return False

        # Start the web server
        self.webserver.start()
        try:
            while self.runnable:
                # Get all waiting events - this always returns a list
                events = self.sc.rtm_read()
                for e in events:
                    self._handle_event(e)
                sleep(0.1)
        except KeyboardInterrupt:
            # On ctrl-c, just exit
            pass
        except:
            self.log.exception('Unhandled exception')

    def stop(self):
        if self.webserver is not None:
            self.webserver.stop()

    def send_message(self, channel, text):
        # This doesn't want the # in the channel name
        if isinstance(channel, SlackChannel):
            channel = channel.channelid
        self.log.debug("Trying to send to %s: %s", channel, text)
        self.sc.rtm_send_message(channel, text)

    def send_im(self, user, text):
        if isinstance(user, SlackUser):
            user = user.userid
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
        if user.username in self.config['bot_admins']:
            user.is_admin = True

    def _handle_event(self, event):
        if 'type' not in event:
            # This is likely a notification that the bot was mentioned
            self.log.debug("Received odd event: %s", event)
            return
        e = SlackEvent(sc=self.sc, **event)
        self.log.debug("Received event type: %s", e.type)
        if e.type in self.event_handlers:
            self.event_handlers[e.type](self, e)

    @eventhandler(events='message')
    def _event_message(self, msg):
        self.log.debug("Message.message: %s: %s: %s", msg.channel, msg.user, msg.__dict__)
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
