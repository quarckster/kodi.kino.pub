import json
from typing import List
from typing import TYPE_CHECKING

import xbmcvfs

if TYPE_CHECKING:
    from resources.lib.plugin import Plugin


class SearchHistory:
    def __init__(self, plugin: "Plugin") -> None:
        self.plugin = plugin
        self.history_max_qty = int(self.plugin.settings.history_max_qty)
        self.path = xbmcvfs.translatePath(
            f"special://userdata/addon_data/{self.plugin.PLUGIN_ID}/history"
        )
        self.items: List[str] = []
        self._load_history()

    @property
    def recent(self) -> List[str]:
        return self.items[: self.history_max_qty]

    def save(self, title: str) -> None:
        if title in self.items:
            self.items.remove(title)  # remove duplicates
        self.items.insert(0, title)  # add to top of list
        self._save_history()

    def clean(self) -> None:
        self.items = []
        self._save_history()

    def _load_history(self) -> None:
        with xbmcvfs.File(self.path, "a+") as f:
            try:
                self.items = json.loads(f.read())
            except ValueError:
                self.items = []

    def _save_history(self) -> None:
        with xbmcvfs.File(self.path, "w+") as f:
            f.write(json.dumps(self.items))
