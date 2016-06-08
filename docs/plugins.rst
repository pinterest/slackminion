A brief guide to writing plugins
================================

Plugins are used to add new commands and functionality to your bot.  To start, all plugins should inherit from ``BasePlugin``.  You can use the code below as a starting point for a new plugin. ::

    from slackminion.plugin import cmd, webhook
    from slackminion.plugin.base import BasePlugin


    class ExamplePlugin(BasePlugin):
        """An example plugin"""
        def on_load(self):
            """
            Code here will be executed when the plugin is loaded into the bot.

            You should remove this if you don't need it.
            """
            super(ExamplePlugin, self).on_load()

        def on_unload(self):
            """
            Code here will be executed when the plugin is unloaded from the bot.

            You should remove this if you don't need it.
            """
            super(ExamplePlugin, self).on_unload()

To add a command your bot will respond to, use the ``@cmd`` decorator::

        @cmd()
        def hello(self, msg, args):
            return "Hello world"

Let's take a closer look at what we just did.

* ``@cmd()`` - tells the bot the following function is a command it should listen for.
* ``def hello(self, msg, args):``
    * defines a function called ``hello``, with two parameters.  In general, bot commands start with ``!``.  Any function with the ``@cmd`` decorator will be used to create a command, in the form of ``!<func_name>``.  In our example, the function ``hello`` will execute when a user types ``!hello``.
    * ``msg`` - ``SlackEvent`` object.
    * ``args`` - A list containing everything the user typed after the command, split on space.
* ``return "Hello world"`` - command functions can return a string, which will be sent as a message to the channel where the command was received (could be a channel or an IM).  You can ``return None`` if you don't want the bot to say anything.

Slackminion also supports webhooks.  These allow the bot to receive an HTTP POST request.  To add a webhook, use the ``@webhook`` decorator::

    @webhook('/echo', form_params='foo')
    def web_echo(self, foo):
        self.send_message('general', foo)

Let's take a look at what this does.

* ``@webhook('/echo', form_params='foo')``
    * tells the bot the following function should be registered in the web server
    * ``/echo`` - This is the route to register in the web server.  The syntax is the same as `Flask <http://flask.pocoo.org/docs/0.11/quickstart/#routing>`_.
    * ``form_params='foo'`` - defines what form parameters the bot should extract from the HTTP POST.  This can be a string (for one parameter), or a list (for multiple parameters)
* ``def web_echo(self, foo):`` - defines a function called ``web_echo`` with one parameter.  The parameter name *must* match the parameters listed in ``form_params``
* ``self.send_message('general', foo)`` - sends a message to the channel ``#general`` with the contents of ``foo``.

Plugins can be configured by specifying values in the config.yaml file, under the ``plugin_settings`` key::

    plugin_settings:
      ExamplePlugin:
        foo: bar

The first key under plugin_settings is the plugin name.  This must match the name of your plugin class.  All keys under that are specific to your plugin, and are made available as a dictionary in ``self.config``.  These values are set before ``on_load()`` is called, and are available from any function in your class.