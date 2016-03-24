from ..plugin import BasePlugin, cmd, webhook


class TestPlugin(BasePlugin):

    @cmd()
    def echo(self, msg, args):
        """Simply repeats whatever is said."""
        self.log.debug("Received args: %s", args)
        return ' '.join(args)

    @cmd()
    def xyzzy(self, msg, args):
        """Nothing happens."""
        return "Nothing happens for %s" % msg.user

    @cmd()
    def alert(self, msg, args):
        """Alert everyone."""
        self.send_message(self.config['channel'], '<!here>: something important is going to happen!')
        return None

    @webhook('/echo', form_params='foo')
    def web_echo(self, foo):
        self.send_message(self.config['channel'], foo)
