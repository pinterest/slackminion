from pkgutil import extend_path
from slackminion.plugin.base import BasePlugin

__path__ = extend_path(__path__, __name__)


class BaseStateHandler(BasePlugin):
    def on_load(self):
        # Don't save this plugin's state during save_state()
        self._dont_save = True
        self._state_handler = True

    def load_state(self):
        pass

    def save_state(self, state):
        pass
