import json
import logging
from datetime import datetime


class PluginManager(object):
    def __init__(self, bot, test_mode=False):
        self.bot = bot
        self.config = bot.config
        self.dispatcher = bot.dispatcher
        self.log = logging.getLogger(type(self).__name__)
        self.plugins = []
        self.state_handler = None
        self.test_mode = test_mode

        if self.test_mode:
            self.metrics = {
                'plugins_total': 0,
                'plugins_loaded': 0,
                'load_times': {},
                'plugins_failed': [],
            }

    def load(self):
        import os
        import sys

        # Add plugin dir for extra plugins
        sys.path.append(os.path.join(os.getcwd(), self.config['plugin_dir']))
        if 'plugins' not in self.config:
            self.config['plugins'] = []

        # Add core plugins
        self.config['plugins'].insert(0, 'slackminion.plugins.core.core.Core')

        for plugin_name in self.config['plugins']:
            if self.test_mode:
                plugin_start_time = datetime.now()
                self.metrics['plugins_total'] += 1
            # module_path.plugin_class_name
            module, name = plugin_name.rsplit('.', 1)
            try:
                m = __import__(module, fromlist=[''])
                plugin = getattr(m, name)
                version = getattr(m, 'version', 'latest')
                commit = getattr(m, 'commit', 'HEAD')
            except ImportError:
                self.log.exception("Failed to load plugin %s", name)
                if self.test_mode:
                    self.metrics['plugins_failed'].append(name)
                continue

            # load plugin config if available
            config = {}
            if name in self.config['plugin_settings']:
                config = self.config['plugin_settings'][name]
            try:
                p = plugin(self.bot, config=config)
                p._version = version
                p._commit = commit
                self.dispatcher.register_plugin(p)
                self.plugins.append(p)
                if p._state_handler:
                    self.state_handler = p
                if self.test_mode:
                    self.metrics['plugins_loaded'] += 1
                    self.metrics['load_times'][name] = (datetime.now() - plugin_start_time).total_seconds() * 1000.0
            except:
                self.log.exception("Failed to register plugin %s", name)
                if self.test_mode:
                    self.metrics['plugins_failed'].append(name)

    def connect(self):
        for plugin in self.plugins:
            try:
                plugin.on_connect()
            except:
                self.log.exception('Unhandled exception')

    def save_state(self):
        if self.state_handler is None:
            self.log.warn("Unable to save state, no handler registered")
            return

        state = {}
        savable_plugins = filter(lambda x: x._dont_save is False, self.plugins)
        for p in savable_plugins:
            attr_blacklist = [
                '_bot',
                '_commit',
                '_dont_save',
                '_state_handler',
                '_timer_callbacks',
                '_version',
                'attr_blacklist',
                'config',
                'log',
            ]
            attr_blacklist.extend(getattr(p, 'attr_blacklist', []))
            attrs = {k: v for k, v in p.__dict__.iteritems() if k not in attr_blacklist}
            state[type(p).__name__] = attrs
            self.log.debug("Plugin %s: %s", type(p).__name__, attrs)
        state = json.dumps(state)
        self.log.debug("Sending the following to the handler: %s", state)
        try:
            self.state_handler.save_state(state)
        except:
            self.log.exception("Handler failed to save state")

    def load_state(self):
        if self.state_handler is None:
            self.log.warn("Unable to load state, no handler registered")
            return

        try:
            state = self.state_handler.load_state()
            state = json.loads(state)
        except:
            self.log.exception("Handler failed to load state")
            return

        for p in self.plugins:
            plugin_name = type(p).__name__
            if plugin_name in state:
                self.log.info("Loading state data for %s", plugin_name)
                for k, v in state[plugin_name].iteritems():
                    self.log.debug("%s.%s = %s", plugin_name, k, v)
                    setattr(p, k, v)
