from slackminion.plugin import cmd
from slackminion.plugin.base import BasePlugin


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

        super(AuthManager, self).on_load()

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

        action = args[0]
        acl_name = None
        if len(args) == 1:
            # Only show is allowed to have no arguments
            if action != 'show':
                return "Usage: !acl _action_ _args_"
        else:
            acl_name = args[1]

        # Only 'new' can have an acl name that doesn't exist
        # Also exempt 'show' as 'None' will never be in the acl list
        if action not in ['new', 'show'] and acl_name not in self._acl:
            return "ACL %s does not exist" % acl_name

        valid_actions = ['allow', 'deny', 'remove', 'show', 'new', 'delete']
        if action not in valid_actions:
            return "Valid actions: %s" % ', '.join(valid_actions)

        # allow, deny, remove all require two arguments (acl name, username)
        if action in ['allow', 'deny', 'remove'] and len(args) < 3:
            return "Usage: !acl %s %s _args_" % (action, acl_name)

        if action == "allow":
            if self.acl_allow(acl_name, args[2]):
                return "Added %s to %s (allow)" % (args[2], acl_name)
            return "Failed to add %s to %s (allow)" % (args[2], acl_name)

        elif action == "deny":
            if self.acl_deny(acl_name, args[2]):
                return "Added %s to %s (deny)" % (args[2], acl_name)
            return "Failed to add %s to %s (deny)" % (args[2], acl_name)

        elif action == "remove":
            if self.acl_remove(acl_name, args[2]):
                return "Removed %s from %s (allow and deny)" % (args[2], acl_name)
            return "Failed to remove %s from %s (allow and deny)" % (args[2], acl_name)

        elif action == "show":
            output = self.acl_show(msg.user, acl_name)
            if output is None:
                return "Sorry, couldn't find an acl named '%s'" % acl_name
            return output

        elif action == "new":
            if self.acl_new(acl_name):
                return "Created new acl '%s'" % acl_name
            return "ACL '%s' already exists" % acl_name

        elif action == "delete":
            if self.acl_delete(acl_name):
                return "Deleted acl '%s'" % acl_name
            return "ACL '%s' does not exist" % acl_name

    def acl_allow(self, name, user):
        """Add a user to the given acl allow block."""

        # Clear user from both allow and deny before adding
        if not self.acl_remove(name, user):
            return False

        if name not in self._acl:
            return False

        self._acl[name]['allow'].append(user)
        return True

    def acl_deny(self, name, user):
        """Add a user to the given acl deny block."""
        if not self.acl_remove(name, user):
            return False

        if name not in self._acl:
            return False

        self._acl[name]['deny'].append(user)
        return True

    def acl_remove(self, name, user):
        """Remove a user from the given acl (both allow and deny)."""
        if name not in self._acl:
            return False
        if user in self._acl[name]['allow']:
            self._acl[name]['allow'].remove(user)
        if user in self._acl[name]['deny']:
            self._acl[name]['deny'].remove(user)
        return True

    def acl_show(self, user, name=None):
        """Show current allow and deny blocks for the given acl."""
        if name is None:
            return "%s: The following ACLs are defined: %s" % (user, ', '.join(self._acl.keys()))

        if name not in self._acl:
            return None

        return '\n'.join([
            "%s: ACL '%s' is defined as follows:" % (user, name),
            "allow: %s" % ', '.join(self._acl[name]['allow']),
            "deny: %s" % ', '.join(self._acl[name]['deny'])
        ])

    def acl_new(self, name):
        """Create a new acl."""
        if name in self._acl:
            return False

        self._acl[name] = {
            'allow': [],
            'deny': []
        }
        return True

    def acl_delete(self, name):
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
