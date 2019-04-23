# !/usr/bin/python
# -*- coding: utf-8 -*-

import base64
import json
import pprint
import requests


def _request(url, data):
    data = dict(params=data)
    print data
    if not url.startswith('http'):
        url = prefix + url
    headers = {'Authorization': 'Bearer {0}'.format(access_token), 'Content-Type': 'application/json'}

    respuesta = requests.get(url, headers=headers, **data)
    if respuesta.text and len(respuesta.text) > 0 and respuesta.text != 'null':
        results = respuesta.json()
        return results
    else:
        return None


def _get(url, **kwargs):
    return _request(url, kwargs)


def search(query, limit=10, offset=0, type='track', market=None):
    return _get('search', query=query, limit=limit, offset=offset, type=type, market=market)


def _get_id(type, id):
    fields = id.split('/')
    if len(fields) >= 3:
        itype = fields[-2]
        if type != itype:
            print('expected id of type %s but found type %s %s',
                  type, itype, id)
        return fields[-1]
    return id


def search_playlist_uri(playlist):
    items = search(query=playlist, type='playlist', limit=20)
    if len(items) > 0:
        pprint.pprint(items)
        return items


def user_playlist_tracks(playlist_id=None, fields=None,
                         limit=100, offset=0, market=None):

    plid = _get_id('playlist', playlist_id)
    return _get("playlists/%s/tracks" % (plid),
                limit=limit, offset=offset, fields=fields,
                market=market)


def get_tracks_from_playlist(playlist_url):
    results = user_playlist_tracks(playlist_url, fields="items")
    items = results['items']

    for x in range(0, len(items)):
        pprint.pprint(items[x]['track']['duration_ms'])
        pprint.pprint(items[x]['track']['name'])


#######################################################
# Token

prefix = 'https://api.spotify.com/v1/'

# Consumer Api Keys Spotify
consumer_key = 'cb169bdfb3884a03ba9c68932f87285b'
consumer_secret = '5ad8b30856c64e569685769261fa2689'

OAUTH_TOKEN_URL = 'https://accounts.spotify.com/api/token'
authorization = base64.standard_b64encode(consumer_key + ':' + consumer_secret)

headers = {'Authorization': 'Basic {0}'.format(authorization)}
data = {'grant_type': 'client_credentials'}

s = requests.Session()

respuesta = s.post(OAUTH_TOKEN_URL, headers=headers, data=data)
# print respuesta.status_code

json_respuesta = json.loads(respuesta.content)
# print json_respuesta
access_token = json_respuesta['access_token']

#######################################################
# Get Playlists

playlist = 'https://open.spotify.com/playlist/37i9dQZF1DWXCGnD7W6WDX'

# get_tracks_from_playlist(playlist)
result = search_playlist_uri('Ozuna')
