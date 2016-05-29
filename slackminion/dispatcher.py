import logging

from flask import current_app, request

from slackminion.exceptions import DuplicateCommandError
from slackminion.slack import SlackChannel


class BaseCommand(object):
    def __init__(self, method):
        self.method = method
        self.help = method.__doc__

    def execute(self, *args, **kwargs):
        return self.method(*args, **kwargs)


class PluginCommand(BaseCommand):
    def __init__(self, method):
        super(PluginCommand, self).__init__(method)
        self.acl = method.acl
        self.admin_only = method.admin_only
        self.is_subcmd = method.is_subcmd
        self.while_ignored = method.while_ignored


class WebhookCommand(BaseCommand):
    def __init__(self, method, form_params):
        super(WebhookCommand, self).__init__(method)
        self.form_params = form_params

    def execute(self):
        args = {}
        form_params = self.form_params
        if isinstance(self.form_params, basestring):
            form_params = [self.form_params]
        if form_params is not None:
            for p in form_params:
                if p in request.form:
                    args[p] = request.form[p]
        return self.method(**args)


class MessageDispatcher(object):
    def __init__(self):
        self.log = logging.getLogger(type(self).__name__)
        self.commands = {}
        self.ignored_channels = []

    def push(self, message):
        """
        Takes a SlackEvent, parses it for a command, and runs against registered plugin
        """
        args = self._parse_message(message)
        self.log.debug("Searching for command using chunks: %s", args)
        cmd, msg_args = self._find_longest_prefix_command(args)
        if cmd is not None:
            if message.user is None:
                self.log.debug("Discarded message with no originating user: %s", message)
                return None, None
            sender = message.user.username
            if message.channel is not None:
                sender = "#%s/%s" % (message.channel.name, sender)
            self.log.info("Received from %s: %s, args %s", sender, cmd, msg_args)
            f = self._get_command(cmd, message.user)
            if f:
                if self._is_channel_ignored(f, message.channel):
                    self.log.info("Channel %s is ignored, discarding command %s", message.channel, cmd)
                    return '_ignored_', ""
                return cmd, f.execute(message, msg_args)
            return '_unauthorized_', "Sorry, you are not authorized to run %s" % cmd
        return None, None

    def _parse_message(self, message):
        args = message.text.split(' ')
        return args

    def register_plugin(self, plugin):
        """Registers a plugin and commands with the dispatcher for push()"""
        self.log.info("Registering plugin %s", type(plugin).__name__)
        self._register_commands(plugin)
        plugin.on_load()

    def _register_commands(self, plugin):
        for name in dir(plugin):
            method = getattr(plugin, name)
            if callable(method) and hasattr(method, 'is_cmd'):
                commands = [method.cmd_name]
                if method.aliases is not None:
                    aliases = method.aliases
                    if isinstance(method.aliases, basestring):
                        aliases = [method.aliases]
                    for alias in aliases:
                        commands.append(alias)

                for cmd_name in commands:
                    cmd = '!' + cmd_name
                    if cmd in self.commands:
                        raise DuplicateCommandError(cmd_name)
                    self.log.info("Registered command %s", type(plugin).__name__ + '.' + cmd_name)
                    self.commands[cmd] = PluginCommand(method)
            elif callable(method) and hasattr(method, 'is_webhook'):
                self.log.info("Registered webhook %s", type(plugin).__name__ + '.' + name)
                webhook = WebhookCommand(method, method.form_params)
                with plugin._bot.webserver.app.app_context():
                    current_app.add_url_rule(method.route, method.__name__, webhook.execute, methods=[method.method])

    def ignore(self, channel):
        if isinstance(channel, SlackChannel):
            channel = channel.name
        if channel not in self.ignored_channels:
            self.ignored_channels.append(channel)
            return True
        return False

    def unignore(self, channel):
        if isinstance(channel, SlackChannel):
            channel = channel.name
        if channel in self.ignored_channels:
            self.ignored_channels.remove(channel)
            return True
        return False

    def _find_longest_prefix_command(self, args):
        num_parts = len(args)
        while num_parts > 0:
            cmd = ' '.join(args[0:num_parts])
            if cmd in self.commands:
                return cmd, args[num_parts:]
            num_parts -= 1
        return None, None

    def _get_command(self, cmd, user):
        can_run_cmd = True
        if hasattr(self, 'auth_manager'):
            can_run_cmd = self.auth_manager.admin_check(self.commands[cmd], user)
            if can_run_cmd:
                can_run_cmd = self.auth_manager.acl_check(self.commands[cmd], user)
        if not can_run_cmd:
            self.log.info("User %s is not authorized to run %s", user.username, cmd)
            return None
        return self.commands[cmd]

    def _is_channel_ignored(self, cmd, channel):
        channel_ignored = False
        if channel.name in self.ignored_channels:
            channel_ignored = not cmd.while_ignored
        return channel_ignored
