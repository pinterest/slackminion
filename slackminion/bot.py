import logging

from slackclient import SlackClient
from time import sleep

from dispatcher import MessageDispatcher
from slack import SlackMessage, SlackChannel, SlackUser
from webserver import Webserver


class NotSetupError(Exception):
    def __str__(self):
        return "Bot not setup.  Please run start() before run()."


class Bot(object):
    def __init__(self, config):
        self.config = config
        self.sc = None
        self.log = logging.getLogger(__name__)
        self.dispatcher = MessageDispatcher()
        self.webserver = None
        self.is_setup = False
        self.always_send_dm = []

    def start(self):
        self.load_plugins()
        self.sc = SlackClient(self.config['slack_token'])
        self.webserver = Webserver(self.config['webserver']['host'], self.config['webserver']['port'])

        if 'always_send_dm' in self.config:
            self.always_send_dm = map(lambda x: '!' + x, self.config['always_send_dm'])

        # Rocket is very noisy at debug
        logging.getLogger('Rocket.Errors.ThreadPool').setLevel(logging.INFO)

        self.is_setup = True

    def load_plugins(self):
        import os
        import sys

        # Add plugin dir for extra plugins
        sys.path.append(os.path.join(os.getcwd(), self.config['plugin_dir']))
        if 'plugins' not in self.config:
            self.config['plugins'] = []

        # Add core plugins
        self.config['plugins'].append('slackminion.plugins.core.Core')

        for plugin_name in self.config['plugins']:
            # module_path.plugin_class_name
            module, name = plugin_name.rsplit('.', 1)
            plugin = __import__(module, fromlist=['']).__dict__[name]

            # load plugin config if available
            config = {}
            if name in self.config['plugin_settings']:
                config = self.config['plugin_settings'][name]

            self.dispatcher.register_plugin(plugin(self, config=config))

    def run(self):

        # Fail out if setup wasn't run
        if not self.is_setup:
            raise NotSetupError

        if not self.sc.rtm_connect():
            return False

        # Start the web server
        self.webserver.start()
        try:
            while True:
                # Get all waiting messages - this always returns a list
                messages = self.sc.rtm_read()
                for m in messages:
                    if 'type' not in m:
                        # This is likely a notification that the bot was mentioned
                        self.log.debug("Received odd message: %s", m)
                        continue
                    msg = SlackMessage(sc=self.sc, **m)
                    self.log.debug("Received message type: %s", msg.type)
                    if msg.type == 'message':
                        self.log.debug("Message.message: %s: %s: %s", msg.channel, msg.user, msg.__dict__)
                        cmd, output = self.dispatcher.push(msg)
                        self.log.debug("Output from dispatcher: %s", output)
                        if output:
                            if cmd in self.always_send_dm:
                                self.send_im(msg.user, output)
                            else:
                                self.send_message(msg.channel, output)
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
        if user[0] == 'D':
            channelid = user
        else:
            channelid = self._find_im_channel(user)
        self.send_message(channelid, text)

    def _find_im_channel(self, user):
        resp = self.sc.api_call('im.list')
        channels = filter(lambda x: x['user'] == user, resp['ims'])
        if len(channels) > 0:
            return channels[0]['id']
        resp = self.sc.api_call('im.open', user=user)
        return resp['channel']['id']
