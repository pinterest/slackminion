from operator import itemgetter

from slackminion.plugin import BasePlugin, cmd


class Core(BasePlugin):

    @cmd()
    def help(self, msg, args):
        """Displays help for each command"""
        output = []
        if len(args) == 0:
            commands = sorted(self._bot.dispatcher.commands.items(), key=itemgetter(0))
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
