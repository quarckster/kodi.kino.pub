from typing import Any
from typing import Callable
from typing import Type

import xbmcaddon
import xbmcgui


def popup_error(message: str, time: int = 4000) -> None:
    xbmcgui.Dialog().notification("Ошибка", message, icon=xbmcgui.NOTIFICATION_ERROR, time=time)


def popup_info(message: str, heading: str = "", time: int = 4000) -> None:
    xbmcgui.Dialog().notification(heading, message, icon=xbmcgui.NOTIFICATION_INFO, time=time)


def popup_warning(message: str, heading: str = "", time: int = 4000) -> None:
    xbmcgui.Dialog().notification(heading, message, icon=xbmcgui.NOTIFICATION_WARNING, time=time)


class cached_property:  # noqa
    """A property that is only computed once per instance and then replaces itself with an ordinary
    attribute. Deleting the attribute resets the property.
    """

    def __init__(self, func: Callable) -> None:
        self.func = func

    def __get__(self, obj: object, cls: Type) -> Any:
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


localize = xbmcaddon.Addon().getLocalizedString
