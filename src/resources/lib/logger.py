import xbmc


class Logger(object):
    def __init__(self, plugin):
        self.plugin = plugin

    def _log(self, message, level):
        fmt_message = "[{}]: {}".format(self.plugin.PLUGIN_ID, str(message))
        xbmc.log(fmt_message, level=level)

    def debug(self, message):
        self._log(message, xbmc.LOGDEBUG)

    def info(self, message):
        self._log(message, xbmc.LOGINFO)

    def notice(self, message):
        self._log(message, xbmc.LOGNOTICE)

    def warning(self, message):
        self._log(message, xbmc.LOGWARNING)

    def error(self, message):
        self._log(message, xbmc.LOGERROR)

    def fatal(self, message):
        self._log(message, xbmc.LOGFATAL)
