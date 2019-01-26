import time
from urllib2 import urlopen 

class Speedtest(object):
    def __init__(self, url):
        self.url = url

    def run(self):
        start = time.clock()
        response = urlopen(self.url)
        CHUNK = 1024 * 1024 # 1MiB
        mbs_to_download = 50

        for i in range(mbs_to_download):
            chunk = response.read(CHUNK)
            downloaded = i * CHUNK
            time_passed = time.clock() - start
            speed_kbs = downloaded // time_passed // 1000
            percentage = i * (100 / mbs_to_download)
            yield percentage, speed_kbs
            if not chunk:
                break