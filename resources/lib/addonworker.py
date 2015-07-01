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


__addon__ = xbmcaddon.Addon(id='plugin.video.kino.pub' )
__settings__ = __addon__
__language__ = __addon__.getLocalizedString
__plugin__ = "plugin://plugin.video.kino.pub"

handle = int(sys.argv[1])
xbmcplugin.setContent(handle, 'movie')


def api(action, params={}, url="http://dev.kino.pub/api/v1", timeout=600):
    access_token = __settings__.getSetting('access_token')
    if access_token:
        params['access_token'] = access_token
    params = urllib.urlencode(params)
    xbmc.log("API params: %s, call from %s" % (params, sys.argv[0]))
    try:
        response = urllib2.urlopen("%s/%s?%s" % (url, action, params), timeout=timeout)
        xbmc.log("API NAV link %s/%s?%s" % (url, action, params))
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
    action = action if action else 'index'
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

# Main screen - show type list
def actionIndex(qp):
    xbmc.executebuiltin('Container.SetViewMode(0)')
    response = api('types')
    if response['status'] == 200:
        add_default_headings(qp)
        for i in response['items']:
            li = xbmcgui.ListItem(i['title'].encode('utf-8'))
            #link = get_internal_link('items', {'type': i['id']})
            link = get_internal_link('genres', {'type': i['id']})
            xbmcplugin.addDirectoryItem(handle, link, li, True)
        xbmcplugin.endOfDirectory(handle)
        xbmc.log("Get types complete!")
    else:
        xbmc.log("Get types error! %s" % response)

def actionGenres(qp):
    response = api('genres', {'type': qp.get('type', '')})
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
            if item['type'] not in ['serial', 'docuserial']:
                response = api('items/%s' % item['id'])
                if response['status'] == 200 and 'videos' in response and len(response['videos']) == 1:
                    link = addonutils.get_mlink(response['videos'][0])
                    li.setProperty('IsPlayable', 'true')
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
                for season in response['seasons']:
                    xbmc.log("Season number: %s = %s" % (season['number'], qp['season']))
                    if int(season['number']) == int(qp['season']):
                        for episode_number, episode in enumerate(season['episodes']):
                            episode_number += 1
                            li = xbmcgui.ListItem("%01d. %s" % (episode_number, episode['title'].encode('utf-8')), iconImage=episode['thumbnail'], thumbnailImage=episode['thumbnail'])
                            li.setInfo('Video', addonutils.video_info(item, {
                                'season': int(season['number']),
                                'episode': episode_number
                            }))
                            li.setProperty('IsPlayable', 'true')
                            link = addonutils.get_mlink(episode)
                            xbmcplugin.addDirectoryItem(handle, link, li, False)
                        break
                xbmcplugin.endOfDirectory(handle)
            else:
                for season in response['seasons']:
                    season_title = season['title'].encode('utf-8') if len(season['title']) > 0 else "Сезон %s" % int(season['number'])
                    li = xbmcgui.ListItem(season_title, iconImage=item['posters']['big'], thumbnailImage=item['posters']['big'])
                    li.setInfo('Video', addonutils.video_info(item, {
                        'season': int(season['number']),
                    }))
                    link = get_internal_link('view', {'id': qp['id'], 'season': season['number']})
                    xbmcplugin.addDirectoryItem(handle, link, li, True)
                xbmcplugin.endOfDirectory(handle)
        elif 'videos' in item and len(item['videos']) > 1:
            for video_number, video in enumerate(response['videos']):
                video_number += 1
                li = xbmcgui.ListItem("%01d. %s" % (video_number, video['title'].encode('utf-8')), iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'])
                li.setInfo('Video', addonutils.video_info(item, {
                    'episode': video_number
                }))
                li.setProperty('IsPlayable', 'true')
                link = addonutils.get_mlink(video)
                xbmcplugin.addDirectoryItem(handle, "", li, False)
            xbmcplugin.endOfDirectory(handle)
        else:
            video = response['videos'][0]
            video_number = 0
            li = xbmcgui.ListItem("%01d. %s" % (video_number, video['title'].encode('utf-8')), iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'])
            li.setInfo('Video', addonutils.video_info(item, {
                'episode': video_number
            }))
            link = addonutils.get_mlink(video)
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
        xbmc.log('actionSearch: nav to items')
        qp['title'] = out
        nav_internal_link('items', qp)
    else:
        notice("Введите больше символов для поиска", "Поиск")
        nav_internal_link('index')
