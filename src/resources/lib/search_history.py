# -*- coding: utf-8 -*-
import json

import xbmcvfs


class SearchHistory(object):
    def __init__(self, plugin):
        self.plugin = plugin
        self.history_max_qty = int(self.plugin.settings.history_max_qty)
        self.path = xbmcvfs.translatePath(
            f"special://userdata/addon_data/{self.plugin.PLUGIN_ID}/history"
        )
        self.items = []
        self._load_history()

    @property
    def recent(self):
        return self.items[: self.history_max_qty]

    def save(self, title):
        if title in self.items:
            self.items.remove(title)  # remove duplicates
        self.items.insert(0, title)  # add to top of list
        self._save_history()

    def clean(self):
        self.items = []
        self._save_history()

    def _load_history(self):
        f = xbmcvfs.File(self.path, "a+")
        try:
            self.items = json.loads(f.read())
        except ValueError:
            self.items = []
        f.close()

    def _save_history(self):
        f = xbmcvfs.File(self.path, "w+")
        f.write(json.dumps(self.items))
        f.close()
