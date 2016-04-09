from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
from slackminion.plugin.base import BasePlugin


class BaseStateHandler(BasePlugin):
    def on_load(self):
        # Don't save this plugin's state during save_state()
        self._dont_save = True
        self._state_handler = True

    def load_state(self):
        pass

    def save_state(self, state):
        pass
