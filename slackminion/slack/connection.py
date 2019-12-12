import threading
import slack


class ThreadedRTMClient(slack.RTMClient):
    def __init__(self, *args, **kwargs):
        super(slack.RTMClient, self).__init__(*args, **kwargs)
        self.server = ThreadWebClient(self.token, False)


class ThreadWebClient(slack.WebClient):
    def __init__(self, *args, **kwargs):
        super(ThreadWebClient, self).__init__(*args, **kwargs)
        self.api_call_lock = threading.RLock()

    def api_call(self, *args, **kwargs):
        with self.api_call_lock:
            return super(ThreadWebClient, self).api_call(*args, **kwargs)
