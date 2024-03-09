import json
from typing import TYPE_CHECKING

import xbmc

if TYPE_CHECKING:
    from resources.lib.plugin import Plugin


class XbmcSettings:
    def __init__(self, plugin: "Plugin") -> None:
        self.plugin = plugin

    def get_setting(self, setting_id: str):
        # https://kodi.wiki/view/JSON-RPC_API/v13#Settings.GetSettingValue
        try:
            self.plugin.logger.debug(f"Try to get system setting: {setting_id}")
            response = xbmc.executeJSONRPC(
                "{"
                '"jsonrpc": "2.0",'
                '"method": "Settings.GetSettingValue",'
                '"params": '
                f'{{ "setting": "{setting_id}" }},'
                '"id": 1'
                "}"
            )
            # Response example:
            # { "id": 1, "jsonrpc": "2.0", "result": { "value": "some data" } }
            self.plugin.logger.debug(f"JSON RPC Response: {response}")
            setting = json.loads(str(response))
            return setting["result"]["value"]
        except Exception as exception:
            self.plugin.logger.error(f"JSON RPC Exception: {exception}")
            return None


class XbmcProxySettings(XbmcSettings):
    def proxy_type(self, type: int) -> str:
        proxy_types = {
            0: "http",
            1: "socks4",
            2: "socks4a",
            3: "socks5",
            4: "socks5h",  # SOCKS5 with remote DNS resolving
            5: "https",
        }
        try:
            self.plugin.logger.debug(f"Parsing system proxy type: {type} -> {proxy_types[type]}")
            return proxy_types[type]
        except KeyError:
            self.plugin.logger.warning(f"Proxy type '{type}' is unknown")
            return ""

    @property
    def is_enabled(self) -> bool:
        return self.get_setting("network.usehttpproxy") or False

    @property
    def type(self) -> str:
        return self.proxy_type(int(self.get_setting("network.httpproxytype"))) or ""

    @property
    def host(self) -> str:
        return self.get_setting("network.httpproxyserver") or ""

    @property
    def port(self) -> int:
        return int(self.get_setting("network.httpproxyport")) or 0

    @property
    def username(self) -> str | None:
        return self.get_setting("network.httpproxyusername") or None

    @property
    def password(self) -> str | None:
        return self.get_setting("network.httpproxypassword") or None

    @property
    def is_correct(self):
        return len(self.host) > 3 and self.port > 0

    @property
    def is_http(self) -> bool:
        return self.type in ["http", "https"]

    @property
    def is_socks(self) -> bool:
        return self.type in ["socks4", "socks4a", "socks5", "socks5r"]

    @property
    def is_socks4(self) -> bool:
        return self.type in ["socks4", "socks4a"]

    @property
    def is_socks5(self) -> bool:
        return self.type in ["socks5", "socks5r"]

    @property
    def with_auth(self) -> bool:
        return bool(self.username and self.password)
