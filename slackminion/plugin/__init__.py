from .base import BasePlugin
from .manager import PluginManager


def cmd(admin_only=False, acl='*', aliases=None, while_ignored=False,
        reply_in_thread=False, reply_broadcast=False, *args, **kwargs):
    """
    Decorator to mark plugin functions as commands in the form of !<cmd_name>

    * admin_only - indicates only users in bot_admin are allowed to execute (only used if AuthManager is loaded)
    * acl - indicates which ACL to perform permission checks against (only used if AuthManager is loaded)
    * aliases - register function with additional commands (i.e. !alias1, !alias2, etc)
    * while_ignored - allows a command to be run, even if channel has been !sleep
    * reply_in_thread - determines whether bot replies in the channel or a thread
    * reply_broadcast - if replying in a thread, whether to also send the message to the channel
    """

    def wrapper(func):
        func.is_cmd = True
        func.is_subcmd = len(func.__name__.split('_')) > 1
        func.cmd_name = func.__name__.replace('_', ' ')
        func.admin_only = admin_only
        func.acl = acl
        func.aliases = aliases
        func.while_ignored = while_ignored
        func.cmd_options = {
            'reply_in_thread': reply_in_thread,
            'reply_broadcast': reply_broadcast,
        }
        return func

    return wrapper


def webhook(*args, **kwargs):
    """
    Decorator to mark plugin functions as entry points for web calls

    * route - web route to register, uses Flask syntax
    * method - GET/POST, defaults to POST
    """

    def wrapper(func):
        func.is_webhook = True
        func.route = args[0]
        func.form_params = kwargs.get('form_params', [])
        func.method = kwargs.get('method', 'POST')
        return func

    return wrapper
