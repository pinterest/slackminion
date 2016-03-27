from operator import itemgetter

from slackminion.plugin import BasePlugin, cmd


class Core(BasePlugin):

    @cmd()
    def help(self, msg, args):
        """Displays help for each command"""
        output = []
        if len(args) == 0:
            commands = sorted(self._bot.dispatcher.commands.items(), key=itemgetter(0))
            # Filter commands if auth is enabled, hide_admin_commands is enabled, and user is not admin
            if hasattr(self._bot.dispatcher, '_auth_manager') and \
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
