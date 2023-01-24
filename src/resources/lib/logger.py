import logging
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING

import xbmc
import xbmcvfs

if TYPE_CHECKING:
    from resources.lib.plugin import Plugin

LEVEL_MAP = {
    xbmc.LOGFATAL: logging.CRITICAL,
    xbmc.LOGERROR: logging.ERROR,
    xbmc.LOGWARNING: logging.WARNING,
    xbmc.LOGINFO: logging.INFO,
    xbmc.LOGDEBUG: logging.DEBUG,
}


class Logger:
    def __init__(self, plugin: "Plugin") -> None:
        self.plugin = plugin
        if self.plugin.settings.is_testing:
            self.configure()

    def configure(self) -> None:
        handler = RotatingFileHandler(
            xbmcvfs.translatePath("special://temp/video_kino_pub.log"),
            # 1MB
            maxBytes=1048576,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
        self._logger = logging.getLogger("video.kino.pub")
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.DEBUG)

    def _log(self, message: str, level: str) -> None:
        fmt_message = f"[{self.plugin.PLUGIN_ID}]: {str(message)}"
        xbmc.log(fmt_message, level=level)
        if self.plugin.settings.is_testing:
            self._logger.log(LEVEL_MAP[level], message)

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
