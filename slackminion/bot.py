import logging

from slackclient import SlackClient
from time import sleep

from dispatcher import MessageDispatcher
from slack import SlackMessage


class Bot(object):
    def __init__(self, token):
        self.sc = SlackClient(token)
        self.log = logging.getLogger(__name__)
        self.dispatcher = MessageDispatcher()

    def start(self):
        from config import PLUGINS
        for plugin_name in PLUGINS:
            module, name = plugin_name.rsplit('.', 1)
            plugin = __import__(module, fromlist=['']).__dict__[name]
            self.dispatcher.register_plugin(plugin(self))

        return self.sc.rtm_connect()

    def run(self):
        try:
            while True:
                raw_messages = self.sc.rtm_read()
                for m in raw_messages:
                    if 'type' not in m:
                        self.log.debug("Received odd message: %s", m)
                        continue
                    msg = SlackMessage(sc=self.sc, **m)
                    self.log.debug("Received message type: %s", msg.type)
                    if msg.type == 'message':
                        self.log.debug("Message.message: %s: %s: %s", msg.channel, msg.user, msg.__dict__)
                        output = self.dispatcher.push(msg)
                        self.log.debug("Output from dispatcher: %s", output)
                        if output:
                            self.send_message(msg.channel.channelid, output)
                sleep(0.1)
        except:
            self.log.exception('Unhandled exception')

    def send_message(self, channel, text):
        self.log.debug("Trying to send to %s: %s", channel, text)
        self.sc.rtm_send_message(channel, text)

    def _send(self, message):
        self.sc.rtm_send_message(message.channelid, message.text)
