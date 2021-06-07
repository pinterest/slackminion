from slack import RTMClient


class MyRTMClient(RTMClient):
    """
    Monkey patch the _dispatch_event method in slack.RTMClient in order to restore the type
    """

    async def _dispatch_event(self, event, data=None):
        if type(data) == dict:
            data.update({'type': event})
        return await super()._dispatch_event(event, data)
