import threading

from slackclient.server import Server
from slackclient.client import SlackClient


class ThreadedSlackClient(SlackClient):
    def __init__(self, *args, **kwargs):
        super(ThreadedSlackClient, self).__init__(*args, **kwargs)
        self.server = ThreadedServer(self.token, False)


class ThreadedServer(Server):
    def __init__(self, *args, **kwargs):
        super(ThreadedServer, self).__init__(*args, **kwargs)
        self.api_call_lock = threading.RLock()

    def api_call(self, *args, **kwargs):
        with self.api_call_lock:
            return super(ThreadedServer, self).api_call(*args, **kwargs)
