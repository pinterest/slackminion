# slackminion
A python bot framework for slack

# Plugins
Plugins should inherit from `slackminion.plugin.BasePlugin`

## Configuration
Plugins have two methods which can be overridden to provide start/shutdown functionality, `on_load` and `on_unload`


## Bot Commands
To add a new command in the form of !command, simply add the `@cmd` decorator to any function in your plugin class.  Anything returned from the function is sent to the channel/IM where the command was sent from.
```
@cmd
def function(self, msg, args)
```
* msg: A `SlackEvent` object
* args: A list of arguments specified with the command
* returns: string

## Webhook Commands
To add a new webhook, add the `@webhook(route)` decorator to any function in your plugin class.  The route uses the same syntax as Bottle routes.  Anything returned from the function is sent to the web client.
```
@webhook(route)
def function(self)
```
* returns: string

The webhook decorator has an optional parameter for reading form fields.
```
@webhook(route, form_params='foo')
def function(self, foo)
```
* form_params: A string or list containing expected fields in the web request
* foo: A field specified in form_params
* returns: string

## Timers
Plugins are able to schedule a function to run after some amount of time.

To start a timer
```
self.start_timer(func, duration)
```
* func: A reference to the function to run
* duration: Time in seconds to wait before running

A timer can be stopped if it hasn't fired yet.
```
self.stop_timer(func)
```
* func: The same function specified in `start_timer`
