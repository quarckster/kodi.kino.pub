import uuid

import m3u8
import xbmcgui
import xbmcvfs


def notice(message, heading="", time=4000):
    xbmcgui.Dialog().notification(heading, message, time=time)


def fix_m3u8(uri, logger):
    master_playlist = m3u8.load(uri)
    for playlist in master_playlist.playlists:
        playlist.uri = playlist.absolute_uri
    for media in master_playlist.media:
        media.uri = media.absolute_uri
    path = xbmcvfs.translatePath(f"special://temp/{uuid.uuid4()}.m3u8")
    with xbmcvfs.File(path, "w") as f:
        result = f.write(master_playlist.dumps())
    logger.info(f"temporary hls playlist {path} {'was' if result else 'was not'} created")
    return path
