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
def get_mlink(video, quality='480p', streamFormat='http'):
    qualities = [480, 720, 1080]
    url = ""
    files = video['files']
    files = sorted(files, key= lambda x: x['quality'], reverse=True)
    for f in files:
        if f['quality'] == quality:
            return f['url'][streamFormat]
        #url = f['url'][streamFormat] # if auto quality or other get max quality from available

    #check if auto quality
    if quality.lower() == 'auto':
        return files[-1]['url'][streamFormat]

    for f in files:
        if int(f['quality'].replace('p', '')) <= int(quality.replace('p', '')):
            return f['url'][streamFormat]
        url = f['url'][streamFormat]
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
        'playcount': int(item['views']),
    }
    if extend and type(extend) is dict:
        n = info.copy()
        n.update(extend)
        info = n
    return info
