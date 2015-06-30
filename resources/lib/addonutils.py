#!/usr/bin/python
# -*- coding: utf-8 -*-

def dict_merge(old, new):
    n = old.copy()
    n.update(new)
    return n

# Get media link
#  video - json dict from api call
#  quality - video quality [480p, 720p, 1080p]
def get_mlink(video, quality='480p'):
    url = ""
    for f in video['files']:
        if f['quality'] == quality:
            return f['url']
        url = f['url']
    return url

# Split title by / and return list with two titles (title, originaltitle)
#  title - string
def gen_titles(title):
    _title = title.split('/')
    title, originaltitle = title.split('/') if '/' in title else [_title, ""]
    return [title, originaltitle]

def video_info(item, extend=None):
    title, originaltitle = gen_titles(item['title'])
    info = {
        'year': int(item['year']),
        'genre': ",".join([x['title'] for x in item['genres']]),
        'rating': float(item['rating']),
        'cast': item['cast'].split(","),
        'director': item['director'],
        'plot': item['plot'],
        'title': title,
        'originaltitle': originaltitle,
        'playcount': int(item['views']),
    }
    if extend and type(extend) is dict:
        n = info.copy()
        n.update(extend)
        info = n
    return info