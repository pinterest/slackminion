import logging
import threading

from slackminion.slack import SlackUser, SlackChannel


class BasePlugin(object):
    def __init__(self, bot, **kwargs):
        self.log = logging.getLogger(type(self).__name__)
        self._bot = bot
        self._dont_save = False  # By default, we want to save a plugin's state during save_state()
        self._state_handler = False  # State storage backends should set this to true
        self._timer_callbacks = {}
        self.config = {}
        if 'config' in kwargs:
            self.config = kwargs['config']

    def on_load(self):
        """
        Executes when a plugin is loaded.

        Override this if your plugin needs to do initialization when loading.
        Do not use this to restore runtime changes to variables -- they will be overwritten later on by PluginManager.load_state()
        """
        pass

    def on_unload(self):
        """
        (Not Implemented Yet) Executes when a plugin is unloaded.

        Override this if your plugin needs to do cleanup when unloading.
        """
        pass

    def on_connect(self):
        """
        Executes immediately after connecting to slack.

        Will not fire on reconnects.
        """
        pass

    def send_message(self, channel, text):
        """
        Used to send a message to the specified channel.

        * channel - can be a channel or user
        * text - message to send
        """
        self._bot.send_message(channel, text)

    def start_timer(self, duration, func, *args):
        """
        Schedules a function to be called after some period of time.

        * duration - time in seconds to wait before firing
        * func - function to be called
        * args - arguments to pass to the function
        """
        t = threading.Timer(duration, self._timer_callback, (func, args))
        self._timer_callbacks[func] = t
        t.start()
        self.log.info("Scheduled call to %s in %ds", func.__name__, duration)

    def stop_timer(self, func):
        """
        Stops a timer if it hasn't fired yet

        * func - the function passed in start_timer
        """
        if func in self._timer_callbacks:
            t = self._timer_callbacks[func]
            t.cancel()
            del self._timer_callbacks[func]

    def _timer_callback(self, func, args):
        del self._timer_callbacks[func]
        func(*args)

    def get_user(self, username):
        """
        Utility function to query slack for a particular user

        :param username: The username of the user to lookup
        :return: SlackUser object or None
        """
        if hasattr(self._bot, 'user_manager'):
            user = self._bot.user_manager.get_by_username(username)
            if user:
                return user
            user = SlackUser.get_user(self._bot.sc, username)
            self._bot.user_manager.set(user)
            return user
        return SlackUser.get_user(self._bot.sc, username)

    def get_channel(self, channel):
        """
        Utility function to query slack for a particular channel

        :param channel: The channel name or channelid of the channel to lookup
        :return: SlackChannel object or None
        """
        return SlackChannel.get_channel(self._bot.sc, channel)
