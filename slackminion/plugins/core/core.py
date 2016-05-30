from datetime import datetime
from flask import render_template
from functools import wraps
from operator import itemgetter

from slackminion.plugin import cmd, webhook
from slackminion.plugin.base import BasePlugin
from slackminion.slack import SlackRoom

from . import version
try:
    from . import commit
except ImportError:
    commit = 'HEAD'


def channel_wrapper(f):
    @wraps(f)
    def wrapper(self, msg, args):
        channel = self._get_channel_from_msg_or_args(msg, args)
        if channel is not None:
            return f(self, channel)
        return None
    return wrapper


class Core(BasePlugin):

    @cmd()
    def help(self, msg, args):
        """Displays help for each command"""
        output = []
        if len(args) == 0:
            commands = sorted(self._bot.dispatcher.commands.items(), key=itemgetter(0))
            commands = filter(lambda x: x[1].is_subcmd is False, commands)
            # Filter commands if auth is enabled, hide_admin_commands is enabled, and user is not admin
            if self._should_filter_help_commands(msg.user):
                commands = filter(lambda x: x[1].admin_only is False, commands)
            for name, cmd in commands:
                output.append(self._get_short_help_for_command(name))
        else:
            name = '!' + args[0]
            output = [self._get_help_for_command(name)]
        return '\n'.join(output)

    def _should_filter_help_commands(self, user):
        return hasattr(self._bot.dispatcher, 'auth_manager') \
               and 'hide_admin_commands' in self._bot.config \
               and self._bot.config['hide_admin_commands'] is True \
               and not getattr(user, 'is_admin', False)

    def _get_help_for_command(self, name):
        if name not in self._bot.dispatcher.commands:
            return 'No such command: %s' % name

        helpstr = self._bot.dispatcher.commands[name].help
        if helpstr is None:
            helpstr = "No description provided."
        return helpstr

    def _get_short_help_for_command(self, name):
        helpstr = self._get_help_for_command(name)
        if '.' in helpstr:
            helpstr = helpstr[0:helpstr.find('.') + 1]
        return "*{name}*: {help}".format(name=name, help=helpstr)

    @cmd(admin_only=True)
    def save(self, msg, args):
        """Causes the bot to write its current state to backend."""
        self.send_message(msg.channel, "Saving current state...")
        self._bot.plugins.save_state()
        self.send_message(msg.channel, "Done.")

    @cmd(admin_only=True)
    def shutdown(self, msg, args):
        """Causes the bot to gracefully shutdown."""
        self.log.info("Received shutdown from %s", msg.user.username)
        self._bot.runnable = False
        return "Shutting down..."

    @cmd()
    def whoami(self, msg, args):
        """Prints information about the user and bot version."""
        output = ["Hello %s" % msg.user]
        if hasattr(self._bot.dispatcher, 'auth_manager') and msg.user.is_admin is True:
            output.append("You are a *bot admin*.")
        output.append("Bot version: %s-%s" % (self._bot.version, self._bot.commit))
        return '\n'.join(output)

    @cmd()
    @channel_wrapper
    def sleep(self, channel):
        """Causes the bot to ignore all messages from the channel.

        Usage:
        !sleep [channel name] - ignore the specified channel (or current if none specified)
        """
        self.log.info('Sleeping in %s', channel)
        self._bot.dispatcher.ignore(channel)
        self.send_message(channel, 'Good night')

    @cmd(admin_only=True, while_ignored=True)
    @channel_wrapper
    def wake(self, channel):
        """Causes the bot to resume operation in the channel.

        Usage:
        !wake [channel name] - unignore the specified channel (or current if none specified)
        """
        self.log.info('Waking up in %s', channel)
        self._bot.dispatcher.unignore(channel)
        self.send_message(channel, 'Hello, how may I be of service?')

    @webhook('/status', method='GET')
    def bot_status(self):
        # TODO: Plugins should provide a get_status() or similar that
        # outputs html/dict+template name.  This command should read
        # from that.  The below should be provided by core.
        plugins = [{
            'name': type(x).__name__,
            'version': x._version,
            'commit': x._commit,
            } for x in self._bot.plugins.plugins]

        uptime = datetime.now() - self._bot.bot_start_time
        partial_day = uptime.seconds
        u_hours = partial_day / 3600

        partial_day %= 3600
        u_minutes = partial_day / 60
        u_seconds = partial_day % 60
        context = {
            'bot_name': self._bot.sc.server.username,
            'version': self._bot.version,
            'commit': self._bot.commit,
            'plugins': plugins,
            'uptime': {
                'days': uptime.days,
                'hours': u_hours,
                'minutes': u_minutes,
                'seconds': u_seconds,
            },
        }
        return render_template('status.html', **context)

    def _get_channel_from_msg_or_args(self, msg, args):
        channel = None
        if len(args) == 0:
            if isinstance(msg.channel, SlackRoom):
                channel = msg.channel
        else:
            channel = self.get_channel(args[0])
        return channel
