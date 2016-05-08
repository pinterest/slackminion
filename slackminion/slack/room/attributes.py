class SlackRoomAttribute(object):
    """Represents a room attribute, such as name, creator, topic, etc"""
    def __init__(self):
        self.data = None

    def __get__(self, instance, owner):
        if self.data is None:
            instance._load_extra_attributes()
        return self.data

    def __set__(self, instance, value):
        self.data = value


class SlackRoomTopic(SlackRoomAttribute):
    """Extension of SlackRoomAttribute, makes API call to set topic when __set__ is called"""
    def __set__(self, instance, value):
        prev_value = self.data
        super(SlackRoomTopic, self).__set__(instance, value)
        if prev_value is not None and prev_value != value:
            instance.set_topic(value)
