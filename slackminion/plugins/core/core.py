from operator import itemgetter

from slackminion.plugin import cmd
from slackminion.plugin.base import BasePlugin


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
                if '.' in helpstr:
                    helpstr = helpstr[0:helpstr.find('.')+1]
                if helpstr is None:
                    helpstr = "No description provided."
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
