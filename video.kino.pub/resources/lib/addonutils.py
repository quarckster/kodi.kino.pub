#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc

def dict_merge(old, new):
    n = old.copy()
    n.update(new)
    return n

# Get media link
#  video - json dict from api call
#  quality - video quality [480p, 720p, 1080p]
def get_mlink(video, quality='480p', streamType='http'):
    # Normalize quality param
    def normalize(qual):
        qual = str(qual)
        return int(qual.lower().replace('p', '').replace('3d', '1080'))

    def geturl(url, streamType='http'):
        return url[streamType] if isinstance(url, dict) else url

    qualities = [480, 720, 1080]
    url = ""
    files = video['files']
    files = sorted(files, key= lambda x: normalize(x['quality']), reverse=False)

    #check if auto quality
    if quality.lower() == 'auto':
        return geturl(files[-1]['url'], streamType)

    # manual param quality
    for f in files:
        f['quality'] = normalize(f['quality'])
        if f['quality'] == quality:
            return geturl(f['url'], streamType)
        #url = f['url'][streamType] # if auto quality or other get max quality from available


    for f in reversed(files):
        if normalize(f['quality']) <= normalize(quality):
            return geturl(f['url'], streamType)
        url = geturl(f['url'], streamType)
    return url

def video_info(item, extend=None):
    info = {
        'year': int(item['year']),
        'genre': ",".join([x['title'] for x in item['genres']]),
        'rating': float(item['rating']),
        'cast': item['cast'].split(","),
        'director': item['director'],
        'plot': item['plot'],
        'title': item['title'],
        'duration': item['duration']['average'] if 'duration' in item else None
    }
    if extend and type(extend) is dict:
        n = info.copy()
        n.update(extend)
        info = n
    return info

