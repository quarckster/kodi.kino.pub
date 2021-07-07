import base64
import threading
import urllib
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from pathlib import PosixPath

import m3u8
import xbmc


HOST = "127.0.0.1"
PORT = 48201
QUERY_KEY = "m3u8_url"
REMOVE_IN_HEADERS = ["upgrade", "host"]
REMOVE_OUT_HEADERS = [
    "date",
    "server",
    "transfer-encoding",
    "keep-alive",
    "connection",
    "content-length",
    "content-encoding",
]


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_POST(self):
        self.send_error(404)

    def do_HEAD(self):
        self.send_error(404)

    def get_hls_base_uri(self, hls_playlist_uri):
        parsed = urllib.parse.urlparse(hls_playlist_uri)
        prefix = f"{parsed.scheme}://{parsed.netloc}"
        base_path = str(PosixPath(f"{parsed.path}/.."))
        return urllib.parse.urljoin(prefix, base_path)

    def fix_m3u8(self, content, base_uri):
        master_playlist = m3u8.loads(content)
        master_playlist.base_uri = base_uri
        for playlist in master_playlist.playlists:
            playlist.uri = playlist.absolute_uri
        for media in master_playlist.media:
            media.uri = media.absolute_uri
        return master_playlist.dumps().encode("utf-8")

    def get_m3u8_response(self, url, headers):
        request = urllib.request.Request(url, headers=headers)
        return urllib.request.urlopen(request, timeout=10)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(url.query)
        headers = {}
        for key in self.headers:
            if key.lower() not in REMOVE_IN_HEADERS:
                headers[key] = self.headers[key]
        encoded_url = query[QUERY_KEY][0]
        hls_playlist_uri = base64.urlsafe_b64decode(encoded_url).decode("utf-8")
        base_uri = self.get_hls_base_uri(hls_playlist_uri)
        response = self.get_m3u8_response(hls_playlist_uri, headers)
        content = self.fix_m3u8(response.read().decode("utf-8"), base_uri)
        self.send_response(response.status)
        for key, value in response.getheaders():
            if key.lower() not in REMOVE_OUT_HEADERS:
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)


class ProxyServer(HTTPServer):

    threads = {}

    def start_in_thread(self):
        if self not in self.threads:
            thread = threading.Thread(target=self.serve_forever)
            self.threads[self] = thread
            thread.start()

    @classmethod
    def stop_all_threads(cls):
        xbmc.Monitor().waitForAbort()
        for server, thread in cls.threads.items():
            server.shutdown()
            server.server_close()
            server.socket.close()
            thread.join()


def start():
    ProxyServer((HOST, PORT), RequestHandler).start_in_thread()
