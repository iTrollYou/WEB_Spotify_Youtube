# coding=utf-8

import base64
import json
import pprint
import requests

# Consumer Api Keys Spotify

from requests import api

_session = api
prefix = 'https://api.spotify.com/v1/'

consumer_key = 'e5c792dbc36a4ec8a06e0bd91ef111eb'
consumer_secret = 'a6864aaefd234446b7ad8c5819051da1'

url = 'https://accounts.spotify.com/api/token'
authorization = base64.standard_b64encode(consumer_key + ':' + consumer_secret)

headers = {
    'Authorization': 'Basic {0}'.format(authorization),
}
data = {
    'grant_type': 'client_credentials'
}

respuesta = requests.post(url, headers=headers, data=data)
print respuesta.status_code

json_respuesta = json.loads(respuesta.content)
access_token = json_respuesta['access_token']
print 'Access_Token: ' + access_token


def _request(method, url, data):
    data = dict(params=data)
    if not url.startswith('http'):
        url = prefix + url
    headers = {'Authorization': 'Bearer {0}'.format(access_token), 'Content-Type': 'application/json'}

    respuesta = _session.request(method, url, headers=headers, **data)
    if respuesta.text and len(respuesta.text) > 0 and respuesta.text != 'null':
        results = respuesta.json()
        print()
        return results
    else:
        return None


def _get(url, **kwargs):
    return _request('GET', url, kwargs)


def search(query, limit=10, offset=0, type='track', market=None):
    return _get('search', q=query, limit=limit, offset=offset, type=type, market=market)


#######################################################

artist = 'Carly Rae Jepsen'
result = search(artist)
# id del artista
print (result['tracks']['items'][0]['artists'][0]['id'])

'''
Prueba busqueda
url_search = 'https://api.spotify.com/v1/search'

headers = {
    'Authorization': 'Bearer {0}'.format(access_token),
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
data = {'q': artist,
        'type': 'artist'}

data_encoded = urllib.urlencode(data)

url_search = url_search + '?' + data_encoded

respuesta = requests.get(url_search, headers=headers)
print respuesta.status_code
print respuesta.content

try:
    respuesta.raise_for_status()
    json_respuesta = json.loads(respuesta.content)
    tmp = json_respuesta['artists']['items'][0]['id']
    print tmp

except:
    if respuesta.text and len(respuesta.text) > 0 and respuesta.text != 'null':
        print respuesta.json()['error']['message']
    else:
        print respuesta.url, 'error'

if respuesta.text and len(respuesta.text) > 0 and respuesta.text != 'null':
    results = respuesta.json()
print()
'''
