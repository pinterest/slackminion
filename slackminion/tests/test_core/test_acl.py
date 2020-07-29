from slackminion.plugins.core.acl import AuthManager
from slackminion.dispatcher import MessageDispatcher
from slackminion.tests.fixtures import *


class TestAuthManager(unittest.TestCase):
    PLUGIN_CLASS = AuthManager
    ADMIN_COMMANDS = [
        'acl',
    ]

    def setUp(self, *args):
        self.object = AuthManager(bot=mock.Mock())
        self.object._bot.dispatcher = MessageDispatcher()
        self.object._bot.api_client.users_find.return_value = TestUser()
        self.test_event = SlackEvent(event_type='tests', **test_payload)
        self.test_user = SlackUser(user_info=test_user_response['user'], api_client=self.object._bot.api_client)
        self.test_event.user = self.test_user

    def test_acl(self):
        e = self.test_event
        assert self.object.acl(e, []) == "Usage: !acl show OR !acl _action_ _args_"

    def test_acl_invalid_action(self):
        e = self.test_event
        assert self.object.acl(e, ['not_a_command']) == "Valid actions: allow, deny, remove, show, new, delete"

    def test_acl_new(self):
        self.object.on_load()
        e = self.test_event
        assert self.object.acl_new(e, ['test']) == "Created new acl 'test'"

    def test_acl_new_already_exists(self):
        self.object.on_load()
        e = self.test_event
        self.object.acl_new(e, ['test'])
        assert self.object.acl_new(e, ['test']) == "ACL 'test' already exists"

    def test_acl_delete(self):
        self.object.on_load()
        e = self.test_event
        self.object.acl_new(e, ['test'])
        assert self.object.acl_delete(e, ['test']) == "Deleted acl 'test'"

    def test_acl_delete_does_not_exists(self):
        self.object.on_load()
        e = self.test_event
        assert self.object.acl_delete(e, ['test']) == "ACL 'test' does not exist"

    def test_acl_allow(self):
        self.object.on_load()
        e = self.test_event
        self.object.acl_new(e, ['test'])
        assert self.object.acl_allow(e, ['test', 'testuser']) == "Added testuser to test (allow)"

    def test_acl_allow_nonexist_acl(self):
        self.object.on_load()
        e = self.test_event
        assert self.object.acl_allow(e, ['test', 'testuser']) == "Failed to add testuser to test (allow)"

    def test_acl_deny(self):
        self.object.on_load()
        e = self.test_event
        self.object.acl_new(e, ['test'])
        assert self.object.acl_deny(e, ['test', 'testuser']) == "Added testuser to test (deny)"

    def test_acl_deny_nonexist_acl(self):
        self.object.on_load()
        e = self.test_event
        assert self.object.acl_deny(e, ['test', 'testuser']) == "Failed to add testuser to test (deny)"

    def test_acl_remove(self):
        self.object.on_load()
        e = self.test_event
        self.object.acl_new(e, ['test'])
        self.object.acl_allow(e, ['test', 'testuser'])
        assert self.object.acl_remove(e, ['test', 'testuser']) == "Removed testuser from test (allow and deny)"

    def test_acl_remove_nonexist_acl(self):
        self.object.on_load()
        e = self.test_event
        assert self.object.acl_remove(e, ['test', 'testuser']) == "Failed to remove testuser from test (allow and deny)"

    def test_acl_show_all(self):
        self.object.on_load()
        e = self.test_event
        self.object.acl_show(e, []) == "testuser: The following ACLs are defined: *"

    def test_acl_show_nonexist_acl(self):
        self.object.on_load()
        e = self.test_event
        self.object.acl_show(e, ['test']) == "Sorry, couldn't find an acl named 'test'"

    def test_acl_show_acl(self):
        self.object.on_load()
        e = self.test_event
        self.object.acl_new(e, ['test'])
        self.object.acl_allow(e, ['test', 'testuser'])
        self.object.acl_show(e, ['test']) == "testuser: ACL 'test' is defined as follows:\nallow: testuser\ndeny: "

    def test_admin_check_non_cmd_non_user(self):
        self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
        e = self.test_event
        e.user = mock.Mock()
        cmd = self.object._bot.dispatcher.commands['!abc']
        assert AuthManager.admin_check(cmd, e.user) is True

    def test_admin_check_admin_cmd_non_user(self):
        self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
        test_user = SlackUser(user_info=test_payload['data'], api_client=self.object._bot.api_client)
        test_user.set_admin(False)
        cmd = self.object._bot.dispatcher.commands['!abc']
        cmd.admin_only = True
        self.assertFalse(AuthManager.admin_check(cmd, test_user))

    def test_admin_check_admin_cmd_admin_user(self):
        user = SlackUser(user_info=test_user_response['user'])
        user.set_admin(True)
        self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
        cmd = self.object._bot.dispatcher.commands['!abc']
        cmd.admin_only = True
        assert AuthManager.admin_check(cmd, user) is True

    def test_acl_check_default_allow(self):
        self.object.on_load()
        self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
        cmd = self.object._bot.dispatcher.commands['!abc']
        assert self.object.acl_check(cmd, self.test_user) is True

    def test_acl_check_explicit_allow(self):
        self.object.on_load()
        self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
        cmd = self.object._bot.dispatcher.commands['!abc']
        self.object.add_user_to_allow('*', self.test_user.username)
        assert self.object.acl_check(cmd, self.test_user) is True

    def test_acl_check_explicit_deny(self):
        self.object.on_load()
        self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
        cmd = self.object._bot.dispatcher.commands['!abc']
        self.object.add_user_to_deny('*', self.test_user.username)
        assert self.object.acl_check(cmd, self.test_user) is False

    def test_acl_check_nonexist_acl_fallback(self):
        self.object.on_load()
        self.object._bot.dispatcher.register_plugin(DummyPlugin(self.object._bot))
        cmd = self.object._bot.dispatcher.commands['!abc']
        cmd.acl = 'doesnotexist'
        assert self.object.acl_check(cmd, self.test_user) is True


if __name__ == "__main__":
    unittest.main()
