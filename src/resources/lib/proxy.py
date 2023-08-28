import base64
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from typing import Any
from typing import Dict

import m3u8

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
    def log_message(self, format: str, *args) -> None:
        return

    # noinspection PyPep8Naming,PyUnusedFunction
    def do_POST(self):
        self.send_error(404)

    # noinspection PyPep8Naming,PyUnusedFunction
    def do_HEAD(self):
        self.send_response(200, "Ok")
        self.end_headers()

    # noinspection PyPep8Naming,PyUnusedFunction
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(url.query)
        headers = {}
        for key in self.headers:
            if key.lower() not in REMOVE_IN_HEADERS:
                headers[key] = self.headers[key]
        encoded_url = query[QUERY_KEY][0]
        hls_playlist_uri = base64.urlsafe_b64decode(encoded_url).decode("utf-8")
        response = self.get_m3u8_response(hls_playlist_uri, headers)
        content = self.fix_m3u8(response.read().decode("utf-8"))
        self.send_response(response.status)
        for key, value in response.getheaders():
            if key.lower() not in REMOVE_OUT_HEADERS:
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)

    @staticmethod
    def get_m3u8_response(url, headers):
        request = urllib.request.Request(url, headers=headers)
        return urllib.request.urlopen(request, timeout=10)

    @staticmethod
    def fix_m3u8(content):
        master_playlist = m3u8.loads(content)
        hdr_defined = False
        for index, playlist in enumerate(master_playlist.playlists):
            if playlist.stream_info.codecs.startswith("hvc1"):
                hdr_defined = True

        # Update playlists only if none of playlist is defined as HEVC stream
        if not hdr_defined:
            RequestHandler.update_stream_info(master_playlist.playlists, "stream_info")
            RequestHandler.update_stream_info(
                master_playlist.iframe_playlists, "iframe_stream_info"
            )
        RequestHandler.update_subtitle_info(master_playlist)
        return master_playlist.dumps().encode("utf-8")

    @staticmethod
    def update_subtitle_info(playlist):
        # find base host to be used if subtitles uri is relative
        base_host = None
        for media_index, media in enumerate(playlist.media):
            if media.type == "AUDIO":
                uri = urllib.parse.urlparse(media.uri)
                base_host = uri.scheme + "://" + uri.hostname

        for media_index, media in enumerate(playlist.media):
            if media.type == "SUBTITLES" and media.language is None:
                media.language = media.name[:3]
            if media.uri.startswith("/") and base_host is not None:
                media.uri = base_host + media.uri

    @staticmethod
    def update_stream_info(playlists, stream_info_property_name):
        existed_streams = {}
        for index, playlist in enumerate(playlists):
            if getattr(playlist, stream_info_property_name).codecs == "hvc1.2.4.L150.B0,mp4a.40.2":
                # skip playlist which is already marked as HEVC stream
                continue

            resolution = (
                str(getattr(playlist, stream_info_property_name).resolution[0])
                + "x"
                + str(getattr(playlist, stream_info_property_name).resolution[1])
            )
            # If a stream with the same resolution is occurring more than once,
            # mark its first occurrence as an HEVC stream
            if resolution in existed_streams:
                index_of_first_stream = existed_streams[resolution]
                hdr_stream = playlists[index_of_first_stream]
                # This is alternative(based on bandwidth)
                # to select the playlist which stream must be mark as an HEVC stream

                # first_playlist = master_playlist.playlists[first_index]
                # if first_playlist.stream_info.bandwidth < playlist.stream_info.bandwidth:
                #     hdr_stream = first_playlist
                # else:
                #     hdr_stream = playlist
                getattr(hdr_stream, stream_info_property_name).codecs = "hvc1.2.4.L150.B0,mp4a.40.2"
                getattr(hdr_stream, stream_info_property_name).video_range = "PQ"
            else:
                existed_streams[resolution] = index


class ProxyServer(HTTPServer):
    threads: Dict[Any, threading.Thread] = {}

    @classmethod
    def start_in_thread(cls, plugin):
        proxy = cls((HOST, PORT), RequestHandler)
        thread = threading.Thread(target=proxy.serve_forever)
        cls.threads[proxy] = thread
        plugin.logger.info("Starting proxy thread")
        thread.start()

    @classmethod
    def stop_all_threads(cls, plugin):
        if cls.threads is None:
            return
        for server, thread in cls.threads.items():
            server.shutdown()
            server.server_close()
            server.socket.close()
            thread.join()
            plugin.logger.info("Stopping proxy thread")
        # del cls.threads[server]
        cls.threads.clear()


def start(plugin):
    ProxyServer((HOST, PORT), RequestHandler).start_in_thread(plugin)
    request = urllib.request.Request(f"http://{HOST}:{PORT}", method="HEAD")
    urllib.request.urlopen(request, timeout=5)


def stop(plugin):
    ProxyServer.stop_all_threads(plugin)
