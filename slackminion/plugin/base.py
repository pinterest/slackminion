from six import string_types
import logging
import threading

from slackminion.slack import SlackConversation, SlackUser


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
        Do not use this to restore runtime changes to variables -- they will be overwritten later on by
        PluginManager.load_state()
        """
        return True

    def on_unload(self):
        """
        Executes when a plugin is unloaded.

        Override this if your plugin needs to do cleanup when unloading.
        """
        return True

    def on_connect(self):
        """
        Executes immediately after connecting to slack.

        Will not fire on reconnects.
        """
        return True

    def send_message(self, channel, text, thread=None, reply_broadcast=False, parse=None):
        """
        Used to send a message to the specified channel.

        * channel - can be a channel or user
        * text - message to send
        * thread - thread to reply in
        * reply_broadcast - whether or not to also send the message to the channel
        * parse - Set to "full" for the slack api to linkify names and channels
        """
        self.log.debug('Sending message to channel {} of type {}'.format(channel, type(channel)))
        if isinstance(channel, SlackConversation):
            self._bot.send_message(channel, text, thread, reply_broadcast, parse)
        elif isinstance(channel, string_types):
            if channel[0] == '@':
                self._bot.send_im(channel[1:], text)
            elif channel[0] == '#':
                self._bot.send_message(channel[1:], text, thread, reply_broadcast, parse)
            else:
                self._bot.send_message(channel, text, thread, reply_broadcast, parse)
        else:
            self._bot.send_message(channel, text, thread, reply_broadcast, parse)

    def start_periodic_task(self, duration, func, *args, **kwargs):
        """
        Schedules a function to be called after some period of time.

        * duration - time in seconds to wait before firing
        * func - function to be called
        * args - arguments to pass to the function
        """
        self.log.debug(f"Scheduling periodic task {func.__name__} every {duration}s (args: {args}, kwargs: {kwargs})")
        if self._bot.runnable:
            self._bot.task_manager.start_periodic_task(duration, func, *args, **kwargs)
            self.log.info(f"Successfully scheduled call to {func.__name__} every {duration}")
        else:
            self.log.warning(f"Not scheduling call to {func.__name__} because we're shutting down.")

    def start_timer(self, duration, func, *args, **kwargs):
        """
        Schedules a function to be called after some period of time.

        * duration - time in seconds to wait before firing
        * func - function to be called
        * args - arguments to pass to the function
        """
        self.log.debug(f"Scheduling call to {func.__name__} in {duration}s (args: {args}, kwargs: {kwargs})")
        if self._bot.runnable:
            self._bot.task_manager.start_timer(duration, func, *args, **kwargs)
            self.log.info(f"Successfully scheduled call to {func.__name__} in {duration}")
        else:
            self.log.warning(f"Not scheduling call to {func.__name__} because we're shutting down.")

    def stop_timer(self, func):
        """
        Stops a timer if it hasn't fired yet

        * func - the function passed in start_timer
        """
        self.log.debug('Stopping timer {}'.format(func.__name__))
        self._bot.task_manager.stop_timer(func.__name__)

    def run_async(self, func, *args, **kwargs):
        return self._bot.task_manager.create_and_schedule_task(func, *args, **kwargs)

    def _timer_callback(self, func, args):
        self.log.debug('Executing timer function {}'.format(func.__name__))
        try:
            func(*args)
        except Exception:
            self.log.exception("Caught exception executing timer function: {}".format(func.__name__))

    async def get_user(self, user_id):
        """
        Utility function to query slack for a particular user

        :param user_id: The username of the user to lookup
        :return: SlackUser object or None
        """
        if not hasattr(self._bot, 'user_manager'):
            user = SlackUser(user_id=user_id, api_client=self._bot.api_client)
            await user.load()
            return user

        user = self._bot.user_manager.get_by_username(user_id)
        if user:
            return user
        user = SlackUser(user_id=user_id)
        await user.load()
        self._bot.user_manager.set(user)
        return user

    def get_channel(self, channel):
        """
        Utility function to query slack for a particular channel

        :param channel: The channel name or id of the channel to lookup
        :return: SlackChannel object or None
        """
        return self._bot.get_channel(channel)

    def get_channel_by_name(self, channel_name):
        """
        Utility function to query slack for a particular channel

        :param channel: The channel name of the channel to lookup
        :return: SlackChannel object or None
        """
        return self._bot.get_channel_by_name(channel_name)

    def at_user(self, *args, **kwargs):
        return self._bot.at_user(*args, **kwargs)
