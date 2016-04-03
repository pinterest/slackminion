Bot Components
==============

Bot
---

The ``Bot`` class is the main driver.  It is responsible for setting up the other components, loading plugins, connecting to slack, and receiving and handling slack events.

Message Dispatcher
------------------
The ``MessageDispatcher`` is responsible for parsing messages and calling the correct function to handle commands.  If an Auth Manager has been loaded, the dispatcher will make a call to ``AuthManager.admin_check()`` and ``AuthManager.acl_check()`` prior to executing the function.  If one of the checks fail, the command is not executed and a message is sent to the user.

Auth Manager
------------
Responsible for providing authorization checks for commands.  The bot has two types of checks that can be applied to a function.  One or both can be used.

* Admin Checks:  Users listed in ``config.yaml:bot_admins`` will pass an admin check.  Commands that should be restricted to admins only should set ``admin_only=True`` in their ``@cmd`` decorator.
* ACL Checks:  The default Auth Manager defines ACLs as having an allow block and a deny block.  The order is evaluated as ``allow block --> deny block --> allow all``.  Unless specified, commands will use the default ``*`` ACL.  Commands that wish to use a different ACL should set ``acl='acl_name'`` in their ``@cmd`` decorator.  The default Auth Manager acl evaluation is described below.
    * Allow block: If a user matches, the check passes and no further evaluation is done.
    * Deny block: If a user matches, the check fails and no further evaluation is done.
    * Allow all: The check passes.
* A command can set both ``admin_only=True`` and ``acl='acl_name'``.  In these cases, both checks must pass for the command to execute.
    * This means an user with admin privileges could be denied access to a command if they match in the deny block of the acl
* The default Auth Manager allows the use of ``*`` in the allow and deny blocks.  This will match all users.

User Manager
------------
Responsible for loading and caching user information.  The default User Manager will provide a mapping between slack userid and username.  If an Auth Manager is loaded, the User Manager will also load and set user privilege flags provided by the Auth Manager on the user object.

State Handler
-------------
Loads and saves plugin state information.  Useful for plugins where configuration can be changed during runtime (such as ACLs).  There are currently two backends available:

* File
* Redis

Web Server
----------
The web server handles incoming requests for web hooks.
