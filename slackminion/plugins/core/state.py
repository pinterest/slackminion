import os

from slackminion.plugin import BasePlugin


class BaseStateHandler(BasePlugin):
    def on_load(self):
        # Don't save this plugin's state during save_state()
        self._dont_save = True
        self._state_handler = True

    def load_state(self):
        pass

    def save_state(self, state):
        pass


class FileStateHandler(BaseStateHandler):
    def load_state(self):
        with open(os.path.join(self.config['data_dir'], 'state.json'), 'rb') as f:
            state = f.read()
        return state

    def save_state(self, state):
        with open(os.path.join(self.config['data_dir'], 'state.json'), 'wb') as f:
            f.write(state)
