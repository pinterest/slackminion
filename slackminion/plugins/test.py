from ..plugin import cmd, webhook
from slackminion.plugins.core import version
try:
    from slackminion.plugins.core import commit
except ImportError:
    commit = 'HEAD'
from slackminion.plugin.base import BasePlugin


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

    @cmd()
    def sleep(self, msg, args):
        """Sleep for a bit, then print a message."""
        self.start_timer(5, self._sleep_func)

    @cmd()
    def sleep2(self, msg, args):
        """Sleep for a bit, then echo the message back"""
        self.start_timer(5, self._sleep_func2, msg.channel, ' '.join(args))

    @cmd()
    def lookup(self, msg, args):
        if args[0] == 'channel':
            return 'Found %s' % self.get_channel(args[1])
        elif args[0] == 'user':
            return 'Found %s' % self.get_user(args[1])

    @cmd()
    def topic(self, msg, args):
        channel = msg.channel
        self.log.debug('Current channel topic: %s', channel.topic)
        if len(args) > 0:
            channel.topic = ' '.join(args)

    def _sleep_func(self):
        self.send_message(self.config['channel'], 'Slept for a bit')

    def _sleep_func2(self, channel, text):
        self.send_message(channel, text)


class TestAclPlugin(BasePlugin):

    @cmd(admin_only=True)
    def admincmd(self, msg, args):
        """A command only admins should be able to run."""
        return ':boom:'

    @cmd(acl='test')
    def acltest(self, msg, args):
        """A command only members of 'test' should be able to run."""
        return ':sushi:'

    @cmd(admin_only=True, acl='test')
    def adminacl(self, msg, args):
        """Only admins who are in 'test' should be able to run this."""
        return ':godmode:'
