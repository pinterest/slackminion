from functools import wraps

from slackminion.plugin import cmd
from slackminion.plugin.base import BasePlugin

from . import version
try:
    from . import commit
except ImportError:
    commit = 'HEAD'


def user_mgt_command(f):
    @wraps(f)
    def wrapper(self, msg, args):
        if len(args) < 2:
            return "Usage: !%s *acl_name* *username*" % f.__name__.replace('_', ' ')
        name, user = args
        return f(self, name, user)
    return wrapper


def acl_mgt_command(f):
    @wraps(f)
    def wrapper(self, msg, args):
        if len(args) < 1:
            return "Usage: !%s *acl_name*" % f.__name__.replace('_', ' ')
        name = args[0]
        return f(self, name)
    return wrapper


class AuthManager(BasePlugin):
    """Basic Authorization Plugin"""
    def on_load(self):

        # Hook into the dispatcher to receive acl checks
        setattr(self._bot.dispatcher, 'auth_manager', self)

        # Setup default ACL
        # ACL Rule Ordering (first match)
        # Allow Rule --> Deny Rule --> Allow All
        self._acl = {
            '*': {
                'allow': [],
                'deny': []
            },
        }

        return super(AuthManager, self).on_load()

    @cmd(admin_only=True)
    def acl(self, msg, args):
        """ACL Management.

        Usage:
        !acl _action_ [args]

        Actions:
        new _acl_ - Create a new ACL
        delete _acl_ - Delete an ACL

        allow _acl_ _user_ - Add user to the acl allow block
        deny _acl_ _user_ - Add user to the acl deny block
        remove _acl_ _user_ - Remove user from acl allow and deny blocks

        show - Show all defined ACLs
        show _acl_ - Show allow and deny blocks of specified ACL
        """
        if len(args) == 0:
            return "Usage: !acl show OR !acl _action_ _args_"

        valid_actions = ['allow', 'deny', 'remove', 'show', 'new', 'delete']
        return "Valid actions: %s" % ', '.join(valid_actions)

    @cmd(admin_only=True)
    @acl_mgt_command
    def acl_new(self, name):
        if self.create_acl(name):
            return "Created new acl '%s'" % name
        return "ACL '%s' already exists" % name

    @cmd(admin_only=True)
    @acl_mgt_command
    def acl_delete(self, name):
        if self.delete_acl(name):
            return "Deleted acl '%s'" % name
        return "ACL '%s' does not exist" % name

    @cmd(admin_only=True)
    @user_mgt_command
    def acl_allow(self, name, user):
        if self.add_user_to_allow(name, user):
            return "Added %s to %s (allow)" % (user, name)
        return "Failed to add %s to %s (allow)" % (user, name)

    @cmd(admin_only=True)
    @user_mgt_command
    def acl_deny(self, name, user):
        if self.add_user_to_deny(name, user):
            return "Added %s to %s (deny)" % (user, name)
        return "Failed to add %s to %s (deny)" % (user, name)

    @cmd(admin_only=True)
    @user_mgt_command
    def acl_remove(self, name, user):
        if self.remove_user_from_acl(name, user):
            return "Removed %s from %s (allow and deny)" % (user, name)
        return "Failed to remove %s from %s (allow and deny)" % (user, name)

    @cmd(admin_only=True)
    def acl_show(self, msg, args):
        """Show current allow and deny blocks for the given acl."""
        name = args[0] if len(args) > 0 else None
        if name is None:
            return "%s: The following ACLs are defined: %s" % (msg.user, ', '.join(self._acl.keys()))

        if name not in self._acl:
            return "Sorry, couldn't find an acl named '%s'" % name

        return '\n'.join([
            "%s: ACL '%s' is defined as follows:" % (msg.user, name),
            "allow: %s" % ', '.join(self._acl[name]['allow']),
            "deny: %s" % ', '.join(self._acl[name]['deny'])
        ])

    def add_user_to_allow(self, name, user):
        """Add a user to the given acl allow block."""

        # Clear user from both allow and deny before adding
        if not self.remove_user_from_acl(name, user):
            return False

        if name not in self._acl:
            return False

        self._acl[name]['allow'].append(user)
        return True

    def add_user_to_deny(self, name, user):
        """Add a user to the given acl deny block."""
        if not self.remove_user_from_acl(name, user):
            return False

        if name not in self._acl:
            return False

        self._acl[name]['deny'].append(user)
        return True

    def remove_user_from_acl(self, name, user):
        """Remove a user from the given acl (both allow and deny)."""
        if name not in self._acl:
            return False
        if user in self._acl[name]['allow']:
            self._acl[name]['allow'].remove(user)
        if user in self._acl[name]['deny']:
            self._acl[name]['deny'].remove(user)
        return True

    def create_acl(self, name):
        """Create a new acl."""
        if name in self._acl:
            return False

        self._acl[name] = {
            'allow': [],
            'deny': []
        }
        return True

    def delete_acl(self, name):
        """Delete an acl."""
        if name not in self._acl:
            return False

        del self._acl[name]
        return True

    @staticmethod
    def admin_check(cmd, user):
        # Commands not needing admin-level access pass
        if not cmd.admin_only:
            return True

        if hasattr(user, 'is_admin'):
            return user.is_admin
        return False

    def acl_check(self, cmd, user):
        effective_acl = cmd.acl
        if effective_acl not in self._acl:
            self.log.warn("Unable to locate ACL %s for %s, defaulting to *", effective_acl, cmd.method.__name__)
            effective_acl = '*'

        if self._check_allow(self._acl[effective_acl], user):
            return True
        if self._check_deny(self._acl[effective_acl], user):
            return False
        return True

    @staticmethod
    def _check_allow(acl, user):
        return '*' in acl['allow'] or user.username in acl['allow']

    @staticmethod
    def _check_deny(acl, user):
        return '*' in acl['deny'] or user.username in acl['deny']
