import xbmcaddon

PLUGIN_ID = xbmcaddon.Addon().getAddonInfo("id")
PLUGIN_URL = "plugin://{}".format(PLUGIN_ID)
