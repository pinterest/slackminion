from .base import BasePlugin
from .manager import PluginManager


def cmd(admin_only=False, acl='*', aliases=None, while_ignored=False, *args, **kwargs):
    """
    Decorator to mark plugin functions as commands in the form of !<cmd_name>

    * admin_only - indicates only users in bot_admin are allowed to execute (only used if AuthManager is loaded)
    * acl - indicates which ACL to perform permission checks against (only used if AuthManager is loaded)
    * aliases - register function with additional commands (i.e. !alias1, !alias2, etc)
    * while_ignored - allows a command to be run, even if channel has been !sleep
    """
    def wrapper(func):
        func.is_cmd = True
        func.admin_only = admin_only
        func.acl = acl
        func.aliases = aliases
        func.while_ignored = while_ignored
        return func
    return wrapper


def webhook(*args, **kwargs):
    """
    Decorator to mark plugin functions as entry points for web calls

    * route - web route to register, uses Bottle syntax
    """
    def wrapper(func):
        func.is_webhook = True
        func.route = args[0]
        func.form_params = kwargs['form_params']
        return func
    return wrapper
