import os

from . import BaseStateHandler


class FileStateHandler(BaseStateHandler):
    def load_state(self):
        with open(os.path.join(self.config['data_dir'], 'state.json'), 'rb') as f:
            state = f.read()
        return state

    def save_state(self, state):
        with open(os.path.join(self.config['data_dir'], 'state.json'), 'wb') as f:
            f.write(state)
