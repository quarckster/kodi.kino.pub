#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib, urllib2, urlparse
import sys
import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
import json
import addonutils
import time

__id__ = 'video.kino.pub'
__addon__ = xbmcaddon.Addon(id=__id__)
__settings__ = xbmcaddon.Addon(id=__id__)
__skinsdir__ = "DefaultSkin"
__language__ = __addon__.getLocalizedString
__plugin__ = "plugin://%s" % __id__

DEFAULT_QUALITY = __settings__.getSetting("video_quality")
DEFAULT_STREAM_TYPE = __settings__.getSetting("stream_type")

_ADDON_PATH =   xbmc.translatePath(__addon__.getAddonInfo('path'))
if (sys.platform == 'win32') or (sys.platform == 'win64'):
    _ADDON_PATH = _ADDON_PATH.decode('utf-8')
handle = int(sys.argv[1])
xbmcplugin.setContent(handle, 'movie')


def api(action, params={}, url="http://api.kino.pub/v1", timeout=600):
    access_token = __settings__.getSetting('access_token')
    if access_token:
        params['access_token'] = access_token
    params = urllib.urlencode(params)
    try:
        response = urllib2.urlopen("%s/%s?%s" % (url, action, params), timeout=timeout)
        #data = json.loads(response.read().decode('string-escape').strip('"'))
        data = json.loads(response.read())
        return data
    except urllib2.HTTPError as e:
        data = json.loads(e.read())
        return data
    except Exception as e:
        print e
        return {
            'status': 105,
            'name': 'Name Not Resolved',
            'message': 'Name not resolved',
            'code': 0
        }

# Form internal link for plugin navigation
def get_internal_link(action, params={}):
    global __plugin__
    params = urllib.urlencode(params)
    return "%s/%s?%s" % (__plugin__, action, params)

def nav_internal_link(action, params={}):
    xbmc.executebuiltin('Container.Update(%s)' % get_internal_link(action, params))

def notice(message, heading):
    xbmc.executebuiltin('XBMC.Notification("%s", "%s")' % (heading, message))

def route():
    global __plugin__

    current = sys.argv[0]
    qs = sys.argv[2]
    action = current.replace(__plugin__, '').lstrip('/')
    action = action if action else 'login'
    actionFn = 'action' + action.title()
    qp = get_params(qs)

    globals()[actionFn](qp)


# Parse query string params into dict
def get_params(qs):
    qs = qs.replace('?', '').split('/')[-1]
    params = {}
    for i in qs.split('&'):
        if '=' in i:
            k,v = i.split('=')
            params[k] = v
    return params



# Entry point
def init():
    route()

"""
 Actions
"""

# qp - dict, query paramters
# fmt - show format
#  s - show search
#  l - show last
def add_default_headings(qp, fmt="sl"):
    if 's' in fmt:
        li = xbmcgui.ListItem('[COLOR FFFFF000]Поиск[/COLOR]')
        xbmcplugin.addDirectoryItem(handle, get_internal_link('search', qp), li, False)
    if 'l' in fmt:
        li = xbmcgui.ListItem('[COLOR FFFFF000]Последние[/COLOR]')
        xbmcplugin.addDirectoryItem(handle, get_internal_link('items', qp), li, True)

def actionLogin(qp):
    import authwindow as auth
    au = auth.Auth(__settings__)
    # check if auth works
    response = api('types')
    if response['status'] in [400, 401]:
        status, response = au.get_token(refresh=True)
        if status == au.EXPIRED:
            au.reauth()
    access_token = __settings__.getSetting('access_token')
    device_code = __settings__.getSetting('device_code')
    access_token_expire = __settings__.getSetting('access_token_expire')
    if device_code or (not device_code and not access_token):
        wn = auth.AuthWindow("auth.xml", _ADDON_PATH, __skinsdir__, settings=__settings__)
        wn.doModal()
        del wn
    if access_token and not device_code:
        # Check if our token need refresh
        access_token_expire = __settings__.getSetting('access_token_expire')
        if access_token_expire and int(float(access_token_expire)) - int(time.time()) <= 3600:
            # refresh access token here
            au.get_token(refresh=True)
    # quick test api
    nav_internal_link('index')

# Main screen - show type list
def actionIndex(qp):
    xbmc.executebuiltin('Container.SetViewMode(0)')
    response = api('types')
    if response['status'] == 200:
        add_default_headings(qp)
        for i in response['items']:
            li = xbmcgui.ListItem(i['title'].encode('utf-8'))
            #link = get_internal_link('items', {'type': i['id']})
            xbmc.log("Adding item to index %s - %s" % (i['title'], i['id']))
            link = get_internal_link('genres', {'type': i['id']})
            xbmcplugin.addDirectoryItem(handle, link, li, True)
        xbmcplugin.endOfDirectory(handle)

def actionGenres(qp):
    response = api('genres', {'type': qp.get('type', '')})
    xbmc.log("Genre types is %s" % qp.get('type'],''))
    if response['status'] == 200:
        add_default_headings(qp)
        for genre in response['items']:
            li = xbmcgui.ListItem(genre['title'].encode('utf-8'))
            link = get_internal_link('items', {'type': qp.get('type'), 'genre': genre['id']})
            xbmcplugin.addDirectoryItem(handle, link, li, True)
        xbmcplugin.endOfDirectory(handle)
    else:
        notice(response['message'], response['name'])

# List items with pagination
#  qp - dict, query parameters for item filtering
#   title - filter by title
#   type - filter by type
#   category - filter by categroies
#   page - filter by page
def actionItems(qp):
    response = api('items', qp)
    if response['status'] == 200:
        pagination = response['pagination']
        add_default_headings(qp, "s")

        # Fill list with items
        for item in response['items']:
            isdir = True if item['type'] in ['serial', 'docuserial'] else False
            link = get_internal_link('view', {'id': item['id']})
            li = xbmcgui.ListItem(item['title'].encode('utf-8'), iconImage=item['posters']['big'], thumbnailImage=item['posters']['big'])
            li.setInfo('Video', addonutils.video_info(item))
            # If not serials or multiseries movie, create playable item
            if item['type'] not in ['serial', 'docuserial']:
                response2 = api('items/%s' % item['id'])
                if response2['status'] == 200:
                    full_item = response2['item']
                    if 'videos' in full_item and len(full_item['videos']) == 1:
                        link = addonutils.get_mlink(full_item['videos'][0], quality=DEFAULT_QUALITY, streamType=DEFAULT_STREAM_TYPE)
                        li.setProperty('IsPlayable', 'true')
                        isdir = False
                    else:
                        link = get_internal_link('view', {'id': item['id']})
                        isdir = True
            xbmcplugin.addDirectoryItem(handle, link, li, isdir)

        # Add "next page" button
        if (int(pagination['current'])) + 1 <= int(pagination['total']):
            qp['page'] = int(pagination['current'])+1
            li = xbmcgui.ListItem("[COLOR FFFFF000]Вперёд[/COLOR]")
            link = get_internal_link("items", qp)
            xbmcplugin.addDirectoryItem(handle, link, li, True)
        xbmcplugin.endOfDirectory(handle)
    else:
        notice(response['message'], response['name'])

# Show items
# If item type is movie with more than 1 episodes - show those episodes
# If item type is serial, docuserial - show seasons
#  if parameter season is set - show episodes
# Otherwise play content
def actionView(qp):
    response = api('items/%s' % qp['id'])
    if response['status'] == 200:
        item = response['item']
        # If serial instance or multiseries film show navigation, else start play
        if item['type'] in ['serial', 'docuserial']:
            if 'season' in qp:
                for season in item['seasons']:
                    if int(season['number']) == int(qp['season']):
                        for episode_number, episode in enumerate(season['episodes']):
                            episode_number += 1
                            li = xbmcgui.ListItem("%01d. %s" % (episode_number, episode['title'].encode('utf-8')), iconImage=episode['thumbnail'], thumbnailImage=episode['thumbnail'])
                            li.setInfo('Video', addonutils.video_info(item, {
                                'season': int(season['number']),
                                'episode': episode_number
                            }))
                            li.setProperty('IsPlayable', 'true')
                            link = addonutils.get_mlink(episode, quality=DEFAULT_QUALITY, streamType=DEFAULT_STREAM_TYPE)
                            xbmcplugin.addDirectoryItem(handle, link, li, False)
                        break
                xbmcplugin.endOfDirectory(handle)
            else:
                for season in item['seasons']:
                    season_title = "Сезон %s" % int(season['number'])
                    li = xbmcgui.ListItem(season_title, iconImage=item['posters']['big'], thumbnailImage=item['posters']['big'])
                    li.setInfo('Video', addonutils.video_info(item, {
                        'season': int(season['number']),
                    }))
                    link = get_internal_link('view', {'id': qp['id'], 'season': season['number']})
                    xbmcplugin.addDirectoryItem(handle, link, li, True)
                xbmcplugin.endOfDirectory(handle)
        elif 'videos' in item and len(item['videos']) > 1:
            for video_number, video in enumerate(item['videos']):
                video_number += 1
                li = xbmcgui.ListItem("%01d. %s" % (video_number, video['title'].encode('utf-8')), iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'])
                li.setInfo('Video', addonutils.video_info(item, {
                    'episode': video_number
                }))
                li.setProperty('IsPlayable', 'true')
                link = addonutils.get_mlink(video, quality=DEFAULT_QUALITY, streamType=DEFAULT_STREAM_TYPE)
                xbmcplugin.addDirectoryItem(handle, link, li, False)
            xbmcplugin.endOfDirectory(handle)
        else:
            video = item['videos'][0]
            video_number = 0
            li = xbmcgui.ListItem("%01d. %s" % (video_number, video['title'].encode('utf-8')), iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'])
            li.setInfo('Video', addonutils.video_info(item, {
                'episode': video_number
            }))
            link = addonutils.get_mlink(video, quality=DEFAULT_QUALITY, streamType=DEFAULT_STREAM_TYPE)
            li.setProperty('IsPlayable', 'true')


def actionSearch(qp):
    kbd = xbmc.Keyboard()
    kbd.setDefault('')
    kbd.setHeading('Поиск')
    kbd.doModal()
    out=''
    if kbd.isConfirmed():
        out = kbd.getText()
    if len(out.decode('utf-8')) >= 3:
        if 'page' in qp:
            qp['page'] = 1
        qp['title'] = out
        nav_internal_link('items', qp)
    else:
        notice("Введите больше символов для поиска", "Поиск")
        nav_internal_link('index')
