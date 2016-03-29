import json
import logging
import threading
from datetime import datetime


def cmd(admin_only=False, acl='*', aliases=None, *args, **kwargs):
    def wrapper(func):
        func.is_cmd = True
        func.admin_only = admin_only
        func.acl = acl
        func.aliases = aliases
        return func
    return wrapper


def webhook(*args, **kwargs):
    def wrapper(func):
        func.is_webhook = True
        func.route = args[0]
        func.form_params = kwargs['form_params']
        return func
    return wrapper


class BasePlugin(object):
    def __init__(self, bot, **kwargs):
        self.log = logging.getLogger(__name__)
        self._bot = bot
        self._dont_save = False  # By default, we want to save a plugin's state during save_state()
        self._state_handler = False  # State storage backends should set this to true
        self._timer_callbacks = {}
        self.config = {}
        if 'config' in kwargs:
            self.config = kwargs['config']

    def on_load(self):
        pass

    def on_unload(self):
        pass

    def send_message(self, channel, text):
        self._bot.send_message(channel, text)

    def start_timer(self, func, duration):
        t = threading.Timer(duration, self._timer_callback, (func,))
        self._timer_callbacks[func] = t
        t.start()

    def stop_timer(self, func):
        if func in self._timer_callbacks:
            t = self._timer_callbacks[func]
            t.cancel()
            del self._timer_callbacks[func]

    def _timer_callback(self, func):
        del self._timer_callbacks[func]
        func()


class PluginManager(object):
    def __init__(self, bot, test_mode=False):
        self.bot = bot
        self.config = bot.config
        self.dispatcher = bot.dispatcher
        self.log = logging.getLogger(__name__)
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
        self.config['plugins'].insert(0, 'slackminion.plugins.core.Core')

        for plugin_name in self.config['plugins']:
            if self.test_mode:
                plugin_start_time = datetime.now()
                self.metrics['plugins_total'] += 1
            # module_path.plugin_class_name
            module, name = plugin_name.rsplit('.', 1)
            try:
                plugin = __import__(module, fromlist=['']).__dict__[name]
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

    def save_state(self):
        if self.state_handler is None:
            self.log.warn("Unable to save state, no handler registered")
            return

        state = {}
        savable_plugins = filter(lambda x: x._dont_save is False, self.plugins)
        for p in savable_plugins:
            attr_blacklist = [
                '_bot',
                '_dont_save',
                '_state_handler',
                '_timer_callbacks',
                'config',
                'log',
            ]
            attrs = {k: v for k, v in p.__dict__.iteritems() if k not in attr_blacklist}
            state[p.__class__.__name__] = attrs
            self.log.debug("Plugin %s: %s", p.__class__.__name__, attrs)
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
            plugin_name = p.__class__.__name__
            if plugin_name in state:
                self.log.info("Loading state data for %s", plugin_name)
                for k, v in state[plugin_name].iteritems():
                    self.log.debug("%s.%s = %s", plugin_name, k, v)
                    setattr(p, k, v)
