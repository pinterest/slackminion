from acl import AuthManager
from core import Core
from slackminion import version
try:
    from slackminion import commit
except ImportError:
    commit = 'HEAD'
from user import UserManager
