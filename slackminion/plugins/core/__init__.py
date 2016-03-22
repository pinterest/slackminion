from operator import itemgetter
from slackminion.plugin import BasePlugin, cmd


class Core(BasePlugin):

    @cmd()
    def help(self, msg, args):
        """Displays help for each command"""
        output = []
        commands = sorted(self._bot.dispatcher.commands.items(), key=itemgetter(0))
        for name, cmd in commands:
            helpstr = cmd.help
            if helpstr is None:
                helpstr = "No description provided"
            output.append("*%s*: %s" % (name, helpstr))
        return '\n'.join(output)
