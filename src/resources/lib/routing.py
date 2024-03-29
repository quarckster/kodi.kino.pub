import re
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union
from urllib.parse import urlencode
from urllib.parse import urlunsplit

import xbmc
import xbmcvfs

if TYPE_CHECKING:
    from resources.lib.plugin import Plugin


class RoutingException(Exception):
    pass


class Routing:
    def __init__(self, plugin: "Plugin") -> None:
        self._rules: Dict[Callable, List[UrlRule]] = {}
        self.plugin = plugin

    def route_for(self, path: str) -> Optional[Callable]:
        if path.startswith(self.plugin.PLUGIN_URL):
            path = path.split(self.plugin.PLUGIN_URL, 1)[1]

        for view_fun, rules in self._rules.items():
            for rule in rules:
                if rule.match(path) is not None:
                    return view_fun
        return None

    def build_url(self, func_name: str, *args, **kwargs) -> str:
        path = "/".join([func_name] + [str(arg) for arg in args])
        return urlunsplit(("plugin", self.plugin.PLUGIN_ID, path, urlencode(kwargs), ""))

    def add_kwargs_to_url(self, **kwargs) -> str:
        self.plugin.kwargs.update(kwargs)
        query_params = urlencode(self.plugin.kwargs)
        return urlunsplit(("plugin", self.plugin.PLUGIN_ID, self.plugin.path, query_params, ""))

    def route(self, pattern: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            self.add_route(func, pattern)
            return func

        return decorator

    def add_route(self, func: Callable, pattern: str) -> None:
        rule = UrlRule(pattern)
        if func not in self._rules:
            self._rules[func] = []
        self._rules[func].append(rule)

    def redirect(self, path: str) -> None:
        xbmc.executebuiltin(f"Container.Update({path})")

    def dispatch(self, path: str) -> None:
        for view_func, rules in self._rules.items():
            for rule in rules:
                kwargs = rule.match(path)
                if kwargs is not None:
                    self.plugin.logger.debug(
                        f"Dispatching to '{view_func.__name__}', args: {kwargs}"
                    )
                    view_func(**kwargs)
                    return
        raise RoutingException(f'No route to path "{path}"')

    def build_icon_path(self, name: str) -> str:
        """Build a path to an icon according to its name"""
        return xbmcvfs.translatePath(
            f"special://home/addons/{self.plugin.PLUGIN_ID}/resources/media/{name}.png"
        )


class UrlRule:
    def __init__(self, pattern: str) -> None:
        kw_pattern = r"<(?:[^:]+:)?([A-z]+)>"
        self._pattern = re.sub(kw_pattern, "{\\1}", pattern)
        self._keywords = re.findall(kw_pattern, pattern)

        p = re.sub("<([A-z]+)>", "<string:\\1>", pattern)
        p = re.sub("<string:([A-z]+)>", "(?P<\\1>[^/]+?)", p)
        p = re.sub("<path:([A-z]+)>", "(?P<\\1>.*)", p)
        self._compiled_pattern = p
        self._regex = re.compile(f"^{self._compiled_pattern}$")

    def match(self, path: str) -> Optional[Dict[str, Union[str, Any]]]:
        match = self._regex.search(path)
        return match.groupdict() if match else None

    def make_path(self, *args: List[str], **kwargs: Dict[str, str]) -> Optional[str]:
        if args and kwargs:
            return None
        if args:
            try:
                return re.sub(r"{[A-z]+}", r"{}", self._pattern).format(args)
            except TypeError:
                return None

        url_kwargs = {k: v for k, v in kwargs.items() if k in self._keywords}
        qs_kwargs = {k: v for k, v in kwargs.items() if k not in self._keywords}

        query = f"?{urlencode(qs_kwargs)}" if qs_kwargs else ""
        try:
            return self._pattern.format(**url_kwargs) + query
        except KeyError:
            return None

    def __repr__(self) -> str:
        return f"UrlRule(pattern={self._pattern}, keywords={self._keywords})"
