from six import string_types
from flask import current_app, request
from slackminion.exceptions import DuplicateCommandError
from slackminion.slack.conversation import SlackConversation
import unicodedata
from slackminion.utils.util import format_docstring, strip_formatting
import logging
import inspect
import re


class BaseCommand(object):
    def __init__(self, method):
        self.method = method
        self.help = method.__doc__

    @property
    def short_help(self):
        if self.help:
            if '.' in self.help:
                return self.help[0:self.help.find('.') + 1]
        return "No description provided."

    @property
    def formatted_help(self):
        if self.help:
            return format_docstring(self.help)
        return "No description provided."

    def execute(self, *args, **kwargs):
        return self.method(*args, **kwargs)


class PluginCommand(BaseCommand):
    def __init__(self, method):
        super(PluginCommand, self).__init__(method)
        self.acl = method.acl
        self.admin_only = method.admin_only
        self.is_subcmd = method.is_subcmd
        self.while_ignored = method.while_ignored
        self.cmd_options = method.cmd_options
        self.is_async = inspect.iscoroutinefunction(method)


class WebhookCommand(BaseCommand):
    def __init__(self, method, form_params):
        super(WebhookCommand, self).__init__(method)
        self.form_params = form_params

    def execute(self):
        args = {}
        form_params = self.form_params
        if isinstance(self.form_params, string_types):
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
        self.ignored_events = ['message_replied', 'message_changed']

    async def push(self, event, dev_mode=False):
        """
        Takes a SlackEvent, parses it for a command, and runs against registered plugin
        """
        self.log.debug(event)
        if self._ignore_event(event):
            return None, None, None
        args = self._parse_message(event)

        # commands will always start with !
        if not args[0].startswith('!'):
            return None, None, None

        self.log.debug("Searching for command using chunks: %s", args)
        cmd, msg_args = self._find_longest_prefix_command(args)
        if cmd is not None:
            if event.user is None:
                self.log.debug("Discarded message with no originating user: %s", event)
                return None, None, None

            if event.channel is not None:
                sender = "#%s/%s" % (event.channel.name, event.user.formatted_name)
            else:
                sender = event.user.slack_user.formatted_name
            self.log.info(f'Received from {sender}: {cmd}, args {msg_args}')
            f = self._get_command(cmd, event.user)
            if f:
                if self._is_channel_ignored(f, event.channel):
                    self.log.info("Channel %s is ignored, discarding command %s", event.channel, cmd)
                    return '_ignored_', "", None

                # Strip formatting if requested by plugin
                if f.cmd_options.get('strip_formatting'):
                    input_string = ' '.join(msg_args)
                    self.log.debug('Calling strip_format with %s', input_string)
                    input_string = strip_formatting(input_string)
                    self.log.debug('Format Stripped message is %s', input_string)
                    msg_args = input_string.split(' ')
                try:
                    if f.is_async:
                        if not dev_mode:
                            output = await f.execute(event, msg_args)
                        else:
                            output = f'DEV_MODE: Would have run async function {f} with args {msg_args}'
                        return cmd, output, f.cmd_options
                    else:
                        if not dev_mode:
                            output = f.execute(event, msg_args)
                        else:
                            output = f'DEV_MODE: Would have run function {cmd} with args {msg_args}'
                        return cmd, output, f.cmd_options
                except Exception as e:  # noqa we don't want plugins to crash the bot so
                    self.log.exception('Plugin raised exception')
                    output = f"Command failed due to an exception: {str(e)}"
                    return cmd, output, f.cmd_options
            return '_unauthorized_', "Sorry, you are not authorized to run %s" % cmd, None
        return None, None, None

    def _ignore_event(self, message):
        """
        message_replied event is not truly a message event and does not have a message.text
        don't process such events

        commands may not be idempotent, so ignore message_changed events.
        """
        if hasattr(message, 'subtype') and message.subtype in self.ignored_events:
            return True
        return False

    def _parse_message(self, message):
        if message:
            try:
                args = unicodedata.normalize('NFKD', message.text).split(' ')
                return args
            except AttributeError:
                pass
        return []

    def register_plugin(self, plugin):
        """Registers a plugin and commands with the dispatcher for push()"""
        self.log.info("Registering plugin %s", type(plugin).__name__)
        self._register_commands(plugin)
        plugin.on_load()

    def _register_commands(self, plugin):
        possible_commands = [x for x in dir(plugin) if not x.startswith('_')]
        for name in possible_commands:
            method = getattr(plugin, name)
            if callable(method) and hasattr(method, 'is_cmd'):
                commands = [method.cmd_name]
                if method.aliases is not None:
                    aliases = method.aliases
                    if isinstance(method.aliases, string_types):
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
        if channel.is_channel:
            if channel.name not in self.ignored_channels:
                self.ignored_channels.append(channel.name)
                return True
        return False

    def unignore(self, channel):
        if channel.is_channel:
            if channel.name in self.ignored_channels:
                self.ignored_channels.remove(channel.name)
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

