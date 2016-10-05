import pytest
import yaml

from slackminion.bot import Bot
from slackminion.exceptions import NotSetupError
from slackminion.plugins.core import version


class TestBot(object):
    def setup(self):
        with open('config.yaml.example', 'r') as f:
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

    def test_run_without_start(self):
        with pytest.raises(NotSetupError) as e:
            self.object.run()
        assert 'Bot not setup' in str(e)

    def test_handler_slack_reconnect_event(self):
        self.object.reconnect_needed = False
        self.object._event_team_migration_started(None)
        assert self.object.reconnect_needed is True
