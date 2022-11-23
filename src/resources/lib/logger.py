import xbmc

from resources.lib.plugin import Plugin


class Logger:
    def __init__(self, plugin: Plugin) -> None:
        self.plugin = plugin

    def _log(self, message: str, level: str) -> None:
        fmt_message = f"[{self.plugin.PLUGIN_ID}]: {str(message)}"
        xbmc.log(fmt_message, level=level)

    def debug(self, message: str) -> None:
        self._log(message, xbmc.LOGDEBUG)

    def info(self, message: str) -> None:
        self._log(message, xbmc.LOGINFO)

    def warning(self, message: str) -> None:
        self._log(message, xbmc.LOGWARNING)

    def error(self, message: str) -> None:
        self._log(message, xbmc.LOGERROR)

    def fatal(self, message: str) -> None:
        self._log(message, xbmc.LOGFATAL)
