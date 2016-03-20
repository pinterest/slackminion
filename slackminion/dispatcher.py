import logging

from bottle import request, app


class DuplicateCommandError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Command already defined: %s" % self.name


class DuplicatePluginError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Plugin already defined: %s" % self.name


class PluginCommand(object):
    def __init__(self, instance, method):
        self.instance = instance
        self.method = method

    def execute(self, *args, **kwargs):
        return self.method(self.instance, *args, **kwargs)


class WebhookCommand(PluginCommand):
    def __init__(self, instance, method, form_params):
        super(WebhookCommand, self).__init__(instance, method)
        self.form_params = form_params

    def execute(self):
        args = {}
        form_params = self.form_params
        if isinstance(self.form_params, basestring):
            form_params = [self.form_params]
        for p in form_params:
            args[p] = request.forms[p]
        return self.method(self.instance, **args)


class MessageDispatcher(object):
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.commands = {}
        self.plugins = {}

    def push(self, message):
        args = self._parse_message(message)
        cmd = args[0]
        self.log.debug("Received command %s with args %s", cmd, args[1:])
        if cmd[0] == '!':
            cmd = cmd[1:]

            if cmd in self.commands:
                self.log.debug("Executing command %s with args %s", cmd, args[1:])
                return self.commands[cmd].execute(message, *args[1:])

    def _parse_message(self, message):
        args = message.text.split(' ')
        return args

    def register_plugin(self, plugin):
        self.log.info("Registering plugin %s", plugin.__class__.__name__)
        self._register_commands(plugin)
        plugin.on_load()

    def _register_commands(self, plugin):
        for name, method in plugin.__class__.__dict__.iteritems():
            if hasattr(method, 'is_cmd'):
                if name in self.commands:
                    raise DuplicateCommandError(name)
                self.log.info("Registered command %s", plugin.__class__.__name__ + '.' + name)
                self.commands[name] = PluginCommand(plugin, method)
            if hasattr(method, 'is_webhook'):
                self.log.info("Registered webhook %s", plugin.__class__.__name__ + '.' + name)
                webhook = WebhookCommand(plugin, method, method.form_params)
                app().route(method.route, 'POST', webhook.execute)
