# coding=utf-8

# !/usr/bin/env python

import time

import logging
import os

import base64
import json
import pprint

import urllib

from webapp2_extras import sessions
import webapp2
import jinja2

import requests
import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses URLFetch.

requests_toolbelt.adapters.appengine.monkeypatch()

app_id = 'spotytube'
callback_url = 'https://' + app_id + '.appspot.com/oauth_callback'

# Consumer Api Keys Spotify
consumer_key = 'cb169bdfb3884a03ba9c68932f87285b'
consumer_secret = '5ad8b30856c64e569685769261fa2689'

# Google keys
google_secret_key = "1FfMRgteyw6T8b46872U0dgb"
client_id = "990115409802-q9o1n9f5hab5lrlg84l21u2si23m90ph.apps.googleusercontent.com"

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.

        self.session_store = sessions.get_store(request=self.request)
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)
        template = JINJA_ENVIRONMENT.get_template('index.html')

        template_playlist_names = self.session.get('playlist_names')
        template_playlist_songs = self.session.get('tracks_names')

        data = {'playlist_names': template_playlist_names,
                'tracks_names': template_playlist_songs}
        # pprint.pprint(template_playlist_names)
        # pprint.pprint(template_playlist_images)

        self.response.write(template.render(data))

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()


config = {'webapp2_extras.sessions': {'secret_key': 'my-super-secret-key'}}


class MainHandler(BaseHandler):

    def get(self):
        logging.debug('ENTERING MainHandler --->')

        spotify_token = self.session.get('spotify_token')

        if spotify_token is None:
            # Si no hay token
            self.redirect('/LoginAndAuthorize')

        else:
            if is_spotify_token_expired(spotify_token):
                self.redirect('/LoginAndAuthorize')


# Spotify
def is_spotify_token_expired(token_info):
    now = int(time.time())
    return token_info['expires_at'] - now < 60


class LoginAndAuthorizeHandler(BaseHandler):
    token_info = None

    def get(self):
        logging.debug('ENTERING LoginAndAuthorizeHandler --->')

        # Step 1: Obtaining a request token
        token_info = self._get_access_token()

        # and store  values
        self.session['spotify_token'] = token_info
        self.redirect('/')

    def _get_access_token(self):
        token_info = self._request_token()
        token_info = self._add_custom_values_to_token_info(token_info)

        # pprint.pprint(token_info)
        self.token_info = token_info

        return self.token_info

    @staticmethod
    def _request_token():
        authorization = base64.standard_b64encode(consumer_key + ':' + consumer_secret)

        headers = {'User-Agent': 'Google App Engine',
                   'Authorization': 'Basic {0}'.format(authorization)}
        data = {'grant_type': 'client_credentials'}

        spotify_token_url = 'https://accounts.spotify.com/api/token'

        response = requests.post(spotify_token_url, headers=headers, data=data)

        if response.status_code != 200:
            print response.reason
        token_info = response.json()
        return token_info

    def _add_custom_values_to_token_info(self, token_info):
        token_info['expires_at'] = int(time.time()) + token_info['expires_in']
        return token_info


class SearchSpotify(BaseHandler):
    def get(self):

        logging.debug('ENTERING SearchSpotify --->')
        self.spotify_token = self.session['spotify_token']['access_token']
        playlist_id = self.request.get("id")

        # comprobar si es nombre de playlist o url
        type = self.request.get('typesearch')

        if playlist_id is "":
            to_search = self.request.get("search")
            list_playlist = self._search_playlists(to_search)

            self._print_playlists(list_playlist)
            self.redirect('/')
        else:


            playlist_tracks = self.get_tracks_from_playlist(playlist_id)
            self._print_tracks(playlist_tracks)

    def _request(self, url, data):

        headers = {'Authorization': 'Bearer {0}'.format(self.spotify_token),
                   'Content-Type': 'application/json'}

        data = dict(params=data)
        # pprint.pprint(data)
        response = requests.get(url, headers=headers, **data)
        if response.text and len(response.text) > 0 and response.text != 'null':
            return response.json()
        else:
            return None

    def _get(self, url, **kwargs):
        return self._request(url, kwargs)

    def _search(self, query, limit=10, offset=0, type='track', market=None):
        return self._get('https://api.spotify.com/v1/search', q=query, limit=limit, offset=offset,
                         type=type, market=market)

    def _search_playlists(self, playlist):
        items = self._search(query=playlist, type='playlist', limit=9, market='ES', offset=0)
        if len(items) > 0:
            return items

    def playlist_tracks(self, playlist_id=None, fields=None,
                        limit=100, offset=0, market=None):

        plid = self.extract_spotify_id(playlist_id)

        return self._get("https://api.spotify.com/v1/playlists/{0}/tracks".format(plid),
                         limit=limit, offset=offset, fields=fields,
                         market=market)

    def get_tracks_from_playlist(self, playlist_url):

        return self.playlist_tracks(playlist_url, fields="items")['items']

    def _print_playlists(self, list_playlist):
        if list_playlist['playlists']['next'] is not None:
            items = list_playlist['playlists']['items']
            self.session['playlist_names'] = []

            for x in range(0, len(items), 1):
                array = []
                array.append(items[x]['name'])
                array.append(items[x]['images'][0]['url'])
                array.append(items[x]['id'])

                self.session['playlist_names'].append(array)

    def _print_tracks(self, playlist_tracks):
        """
        Posiciones de la array:
        0 -> nombre canción
        1 -> nombre artista
        2 -> nombres de artistas
        3 -> duración(ms)
        4 -> url imagen
        5 -> url preview song
        :param playlist_tracks: Lista de canciones de la playlist
        :return: 
        """""

        self.session['tracks_names'] = []
        for track in playlist_tracks:
            current_track = track['track']
            # pprint.pprint(current_track)
            array = []
            array.append(current_track['name'])

            track_artists = []
            for artist in current_track['artists']:
                track_artists.append(artist['name'])
            featured_artists = ';'.join(track_artists)
            artist = featured_artists.split(';')[0]
            array.append(artist)

            album_artists = []
            for artist in current_track['album']['artists']:
                album_artists.append(artist['name'])
            array.append(album_artists)

            array.append(current_track['duration_ms'])
            array.append(current_track['album']['images'][0]['url'])
            array.append(current_track['preview_url'])

            self.session['tracks_names'].append(array)

        #query = '{0} - {1}'.format(self.session.get('tracks_names')[0][1], self.session.get('tracks_names')[0][0])
        # pprint.pprint(str(query))

    def extract_spotify_id(self, raw_string):
        # print raw_string
        # Input string is an HTTP URL
        if raw_string.endswith("/"):
            raw_string = raw_string[:-1]
        to_trim = raw_string.find("?")

        if not to_trim == -1:
            raw_string = raw_string[:to_trim]
        splits = raw_string.split("/")

        spotify_id = splits[-1]

        return spotify_id


class ShowSongsSpotify(BaseHandler):
    def get(self):
        id = self.request.get('id')
        print id


class LoginAndAuthorizeGoogleHandler(BaseHandler):

    def get(self):
        # Enviar una solicitud de autenticacion a google
        redirect_uri = 'http://localhost:8080/oauth2callback'  # Localhost
        # redirect_uri = 'http://spotytube.appspot.com/oauth2callback'

        server = 'https://accounts.google.com/o/oauth2/v2/auth'

        params = {'client_id': client_id,
                  'response_type': 'code',
                  'scope': 'https://www.googleapis.com/auth/youtube',
                  'redirect_uri': redirect_uri,
                  'access_type': 'offline'}

        headers = {'User-Agent': 'Google App Engine'}

        params_encoded = urllib.urlencode(params)

        response = requests.get(server, headers=headers, params=params_encoded)
        if response.status_code == 200:
            self.redirect(str(response.url))


class OauthCallBackHandler(BaseHandler):
    def get(self):
        # Get code
        code = self.request.get('code')

        # Get token
        redirect_uri = 'http://localhost:8080/oauth2callback'  # Localhost

        headers = {
            'Host': 'www.googleapis.com',
            'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': google_secret_key,
            'grant_type': 'authorization_code'
        }
        response = requests.post("https://www.googleapis.com/oauth2/v4/token", headers=headers, data=data)

        json_respuesta = json.loads(response.content)
        print json_respuesta
        access_token = json_respuesta['access_token']
        # print response.content

        self.session['yt_token'] = access_token
        self.redirect('/')


class YoutubePlaylist(BaseHandler):
    def get(self):
        idPlaylist = self._crear_playlist_('Ed Sheeran')
        videoId = self._buscar_cancion_('Perfect')
        self._anadir_cancion(idPlaylist, videoId)

    def _buscar_cancion_(self, titulo):
        params = {'part': 'snippet',
                  'order': 'relevance',
                  'q': titulo,
                  'type': 'video'}
        params_encoded = urllib.urlencode(params)

        headers = {'Authorization': 'Bearer {0}'.format(self.session['yt_token']),
                   'Accept': 'application/json'}

        response = requests.get("https://www.googleapis.com/youtube/v3/search", headers=headers,
                                params=params_encoded)

        json_respuesta = json.loads(response.content)
        items = json_respuesta['items']
        return items[0]['id']['videoId']

    def _crear_playlist_(self, nombre):
        headers = {'Authorization': 'Bearer {0}'.format(self.session['yt_token']),
                   'Accept': 'application/json',
                   'Content-Type': 'application/json'}

        params = {'part': 'snippet'}
        params_encoded = urllib.urlencode(params)

        data = {'snippet': {'title': nombre}}
        jsondata = json.dumps(data)
        response = requests.post('https://www.googleapis.com/youtube/v3/playlists?' + params_encoded,
                                 headers=headers, data=jsondata)
        json_respuesta = json.loads(response.content)
        return json_respuesta['id']

    def _anadir_cancion(self, playlistId, videoId):
        headers = {'Authorization': 'Bearer {0}'.format(self.session['yt_token']),
                   'Accept': 'application/json',
                   'Content-Type': 'application/json'}
        params = {'part': 'snippet'}
        params_encoded = urllib.urlencode(params)

        data = {'snippet': {'playlistId': playlistId,
                            'resourceId': {
                                'videoId': videoId,
                                'kind': 'youtube#video'}
                            }
                }
        jsondata = json.dumps(data)
        response = requests.post('https://www.googleapis.com/youtube/v3/playlistItems?' + params_encoded,
                                 headers=headers, data=jsondata)


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/LoginAndAuthorize', LoginAndAuthorizeHandler),
    ('/LoginGoogle', LoginAndAuthorizeGoogleHandler),
    ('/oauth2callback', OauthCallBackHandler),
    ('/SearchSpotify', SearchSpotify),
    ('/Playlist', YoutubePlaylist),
    ('/GetSongs', ShowSongsSpotify)

], config=config, debug=True)
