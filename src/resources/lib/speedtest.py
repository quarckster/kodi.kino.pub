# -*- coding: utf-8 -*-
import random
import threading
import timeit
from Queue import Queue
from urllib2 import Request
from urllib2 import urlopen

import xbmcgui


SERVERS = {"ru": {"name": "Россия", "value": 0}, "de": {"name": "Германия", "value": 0}}


def to_mbytes(value):
    return value / 1024 / 1024


class FileGetter(threading.Thread):
    def __init__(self, server, fSize, ckSize, start):
        self.url = "https://{}-speed.streambox.in/garbage.php?r={}&ckSize={}".format(
            server, random.random(), fSize
        )
        self.result = None
        self.starttime = start
        self.ckSize = ckSize
        threading.Thread.__init__(self)

    def run(self):
        self.result = [0]
        try:
            if timeit.default_timer() - self.starttime <= 10:
                request = Request(self.url)
                f = urlopen(request)
                while (
                    1
                    and not shutdown_event.isSet()
                    and timeit.default_timer() - self.starttime <= 20
                ):
                    self.result.append(len(f.read(self.ckSize)))
                    if self.result[-1] == 0:
                        break
                f.close()
        except IOError:
            pass


class BaseDialog(object):
    def __init__(self):
        self.heading = "Тест скорости"
        self.servers = {}

    @property
    def speed_formatted(self):
        s = ""
        for server in self.servers.values():
            s += "{}: [B]{:.2f} Mb/s[/B][CR]".format(server["name"], to_mbytes(server["value"]) * 8)
        return s


class SpeedTestResult(xbmcgui.Dialog, BaseDialog):
    def create(self, servers={}):
        self.servers = servers
        self.textviewer(self.heading, self.speed_formatted + self.info)

    @property
    def info(self):
        return """[CR][B]Рекомендованные скорости для просмотра:[/B]

[B]3-5 Mb/s[/B] для просмотра в разрешении [B]480p[/B]
[B]5-10 Mb/s[/B] для просмотра в разрешении [B]720p[/B]
[B]10+ Mb/s[/B] для просмотра в разрешении [B]1080p[/B]
[B]25-50+ Mb/s[/B] для просмотра в разрешении [B]4K[/B]

[I]*Все скорости указаны для устройства, а не подключения у провайдера[/I]"""


class SpeedTestProgress(xbmcgui.DialogProgress, BaseDialog):
    def create(self, servers={}):
        self.servers = servers
        super(SpeedTestProgress, self).create(self.heading, self.speed_formatted)

    def update(self, location, value, progress=0):
        self.servers[location]["value"] = value
        super(SpeedTestProgress, self).update(int(progress), self.speed_formatted)


class SpeedTest(object):
    def __init__(self, fSize=100, ckSize=65536):
        self.progress = SpeedTestProgress()
        self.result = SpeedTestResult()
        self.fSize = fSize
        self.ckSize = ckSize

    def downloadSpeed(self, location):
        start = timeit.default_timer()

        def producer(q, location):
            thread = FileGetter(location, self.fSize, self.ckSize, start)
            thread.start()
            q.put(thread, True)

        def consumer(q, location):
            thread = q.get(True)
            while thread.isAlive():
                thread.join(timeout=0.1)
                loaded = sum(thread.result)
                speed = loaded / (timeit.default_timer() - start)
                progress = to_mbytes(loaded) / float(self.fSize) * 100
                if self.progress.iscanceled():
                    self.progress.close()
                    shutdown_event.set()
                    break
                self.progress.update(location, speed, progress)
            del thread

        q = Queue(2)
        prod_thread = threading.Thread(target=producer, args=(q, location))
        cons_thread = threading.Thread(target=consumer, args=(q, location))
        prod_thread.start()
        cons_thread.start()
        while cons_thread.isAlive():
            cons_thread.join(timeout=0.1)

    def run(self):

        global shutdown_event
        shutdown_event = threading.Event()

        self.progress.create(SERVERS)

        for location in SERVERS.keys():
            self.downloadSpeed(location)

        if not shutdown_event.isSet():
            self.progress.close()
            self.result.create(self.progress.servers)
