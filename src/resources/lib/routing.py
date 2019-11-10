# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
from urllib import urlencode
from urlparse import parse_qsl
from urlparse import urlsplit
from urlparse import urlunsplit

import xbmc

from resources.lib import logger
from resources.lib import PLUGIN_ID
from resources.lib import PLUGIN_URL
from resources.lib.auth import Auth
from resources.lib.settings import Settings


class RoutingException(Exception):
    pass


class Plugin(object):
    def __init__(self):
        self._rules = {}
        self.path = urlsplit(sys.argv[0]).path or "/"
        self.handle = int(sys.argv[1])
        self.kwargs = dict(parse_qsl(sys.argv[2].lstrip("?")))
        self.base_url = PLUGIN_URL
        self.auth = Auth()
        self.settings = Settings()

    def route_for(self, path):
        if path.startswith(self.base_url):
            path = path.split(self.base_url, 1)[1]

        for view_fun, rules in self._rules.iteritems():
            for rule in rules:
                if rule.match(path) is not None:
                    return view_fun
        return None

    def build_url(self, func_name, *args, **kwargs):
        path = u"/".join([func_name] + map(unicode, list(args)))
        url = urlunsplit(("plugin", PLUGIN_ID, path, urlencode(kwargs), ""))
        return url

    def route(self, pattern):
        def decorator(func):
            self.add_route(func, pattern)
            return func

        return decorator

    def add_route(self, func, pattern):
        rule = UrlRule(pattern)
        if func not in self._rules:
            self._rules[func] = []
        self._rules[func].append(rule)

    def run(self):
        self._dispatch(self.path)

    def redirect(self, path):
        xbmc.executebuiltin("Container.Update({})".format(path))

    def _dispatch(self, path):
        for view_func, rules in self._rules.iteritems():
            for rule in rules:
                kwargs = rule.match(path)
                if kwargs is not None:
                    logger.debug("Dispatching to '{}', args: {}".format(view_func.__name__, kwargs))
                    view_func(**kwargs)
                    return
        raise RoutingException('No route to path "{}"'.format(path))


class UrlRule(object):
    def __init__(self, pattern):
        kw_pattern = r"<(?:[^:]+:)?([A-z]+)>"
        self._pattern = re.sub(kw_pattern, "{\\1}", pattern)
        self._keywords = re.findall(kw_pattern, pattern)

        p = re.sub("<([A-z]+)>", "<string:\\1>", pattern)
        p = re.sub("<string:([A-z]+)>", "(?P<\\1>[^/]+?)", p)
        p = re.sub("<path:([A-z]+)>", "(?P<\\1>.*)", p)
        self._compiled_pattern = p
        self._regex = re.compile("^{}$".format(self._compiled_pattern))

    def match(self, path):
        match = self._regex.search(path)
        return match.groupdict() if match else None

    def make_path(self, *args, **kwargs):
        if args and kwargs:
            return None
        if args:
            try:
                return re.sub(r"{[A-z]+}", r"{}", self._pattern).format(args)
            except TypeError:
                return None

        url_kwargs = {((k, v) for k, v in kwargs.items() if k in self._keywords)}
        qs_kwargs = {((k, v) for k, v in kwargs.items() if k not in self._keywords)}

        query = "?{}".format(urlencode(qs_kwargs)) if qs_kwargs else ""
        try:
            return self._pattern.format(**url_kwargs) + query
        except KeyError:
            return None

    def __str__(self):
        return u"UrlRule(pattern={}, keywords={})".format(self._pattern, self._keywords)


plugin = Plugin()
