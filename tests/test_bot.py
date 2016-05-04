import pytest
import yaml

from slackminion.bot import Bot
from slackminion.plugins.core import version


class TestBot(object):
    def setup(self):
        with open('config.yaml', 'r') as f:
            self.object = Bot(config=yaml.load(f), test_mode=True)

    def teardown(self):
        self.object = None

    def test_init(self):
        assert self.object.version == version
        assert self.object.commit == 'HEAD'

    def test_start(self):
        self.object.start()
        assert self.object.is_setup is True

    def test_stop(self):
        self.object.stop()
