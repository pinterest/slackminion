from builtins import object
import pytest

from slackminion.plugin import BasePlugin, cmd

from .bot import DummyBot
from .slack import DummySlackConnection

EXPECTED_PLUGIN_METHODS = [
    'on_connect',
    'on_load',
    'on_unload',
]





