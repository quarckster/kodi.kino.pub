import time
from urllib2 import urlopen


class Speedtest(object):
    def __init__(self, url):
        self.url = url
        self.chunk_size = 1024 * 1024  # 1MiB
        self.mbs_to_download = 50
        self.start_time = time.clock()

    def _get_percentage_and_speed(self, i):
        downloaded = i * self.chunk_size
        time_passed = time.clock() - self.start_time
        speed_kbs = downloaded // time_passed // 1000
        percentage = i * (float(100) / float(self.mbs_to_download))
        return int(percentage), speed_kbs

    def iter_results(self):
        response = urlopen(self.url)

        for i in range(self.mbs_to_download):
            chunk = response.read(self.chunk_size)
            yield self._get_percentage_and_speed(i)
            if not chunk:
                break
