class DuplicateCommandError(Exception):  # pragma: nocover
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Command already defined: %s" % self.name


class DuplicatePluginError(Exception):  # pragma: nocover
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Plugin already defined: %s" % self.name


class NotSetupError(Exception):  # pragma: nocover
    def __str__(self):
        return "Bot not setup.  Please run start() before run()."
