from slackminion.plugin import BasePlugin, cmd


class AuthManager(BasePlugin):
    """Basic Authorization Plugin"""
    def on_load(self):

        # Hook into the dispatcher to receive acl checks
        setattr(self._bot.dispatcher, '_auth_manager', self)

        # Setup default ACL
        # ACL Rule Ordering (first match)
        # Allow Rule --> Deny Rule --> Allow All
        self.acl = {
            '*': {
                'allow': [],
                'deny': []
            },
        }

        super(AuthManager, self).on_load()

    @cmd(admin_only=True)
    def acl(self, msg, args):
        """ACL Management."""
        pass

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
        if effective_acl not in self.acl:
            self.log.warn("Unable to locate ACL %s for %s, defaulting to *", effective_acl, cmd.method.__name__)
            effective_acl = '*'

        if self._check_allow(self.acl[effective_acl], user):
            return True
        if self._check_deny(self.acl[effective_acl], user):
            return False
        return True

    @staticmethod
    def _check_allow(acl, user):
        return user.username in acl['allow']

    @staticmethod
    def _check_deny(acl, user):
        return user.username in acl['deny']
