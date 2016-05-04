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


class NotSetupError(Exception):
    def __str__(self):
        return "Bot not setup.  Please run start() before run()."
