from operator import itemgetter

from slackminion.plugin import cmd
from slackminion.plugin.base import BasePlugin
from slackminion.slack import SlackRoom


class Core(BasePlugin):

    @cmd()
    def help(self, msg, args):
        """Displays help for each command"""
        output = []
        if len(args) == 0:
            commands = sorted(self._bot.dispatcher.commands.items(), key=itemgetter(0))
            # Filter commands if auth is enabled, hide_admin_commands is enabled, and user is not admin
            if hasattr(self._bot.dispatcher, 'auth_manager') and \
                    'hide_admin_commands' in self._bot.config and \
                    self._bot.config['hide_admin_commands'] is True and \
                    not getattr(msg.user, 'is_admin', False):
                commands = filter(lambda x: x[1].admin_only is False, commands)
            for name, cmd in commands:
                helpstr = cmd.help
                if helpstr is None:
                    helpstr = "No description provided."
                elif '.' in helpstr:
                    helpstr = helpstr[0:helpstr.find('.') + 1]
                output.append("*%s*: %s" % (name, helpstr))
        else:
            name = '!' + args[0]
            if name not in self._bot.dispatcher.commands:
                output = ['No such command: %s' % name]
            else:
                helpstr = self._bot.dispatcher.commands[name].help
                if helpstr is None:
                    helpstr = "No description provided."
                output = [helpstr]
        return '\n'.join(output)

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
    def sleep(self, msg, args):
        """Causes the bot to ignore all messages from the channel.

        Usage:
        !sleep [channel name] - ignore the specified channel (or current if none specified)
        """

        channel = None
        if len(args) == 0:
            if isinstance(msg.channel, SlackRoom):
                channel = msg.channel
        else:
            channel = self.get_channel(args[0])

        if channel is not None:
            self.log.info('Sleeping in %s', channel)
            self._bot.dispatcher.ignore(channel)
            self.send_message(channel, 'Good night')

    @cmd(admin_only=True, while_ignored=True)
    def wake(self, msg, args):
        """Causes the bot to resume operation in the channel.

        Usage:
        !wake [channel name] - unignore the specified channel (or current if none specified)
        """

        channel = None
        if len(args) == 0:
            if isinstance(msg.channel, SlackRoom):
                channel = msg.channel
        else:
            channel = self.get_channel(args[0])

        if channel is not None:
            self.log.info('Waking up in %s', channel)
            self._bot.dispatcher.unignore(channel)
            self.send_message(channel, 'Hello, how may I be of service?')
