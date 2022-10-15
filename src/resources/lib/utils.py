import xbmcgui


def notice(message, heading="", time=4000):
    xbmcgui.Dialog().notification(heading, message, time=time)


class cached_property:  # noqa
    """A property that is only computed once per instance and then replaces itself with an ordinary
    attribute. Deleting the attribute resets the property.
    """

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value
