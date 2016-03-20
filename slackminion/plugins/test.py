from ..plugin import BasePlugin, cmd, webhook


class TestPlugin(BasePlugin):

    @cmd
    def echo(self, msg, *args):
        self.log.debug("Received args: %s", args)
        return ' '.join(args)

    @cmd
    def xyzzy(self, msg, *args):
        return "Nothing happens for %s" % msg.user

    @cmd
    def alert(self, msg, *args):
        self.send_message(self.config['channel'], '<!here>: something important is going to happen!')
        return None

    @webhook('/echo', form_params='foo')
    def web_echo(self, foo):
        self.send_message(self.config['channel'], foo)
