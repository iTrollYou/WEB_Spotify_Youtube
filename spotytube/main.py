# coding=utf-8

# !/usr/bin/env python
import hashlib
import time

import logging
import os

import base64
import json

import random
import urllib
import webbrowser

from webapp2_extras import sessions
import webapp2
import jinja2

import requests
import requests_toolbelt.adapters.appengine

from requests import api

_session = api

# Use the App Engine Requests adapter. This makes sure that Requests uses URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()

app_id = 'spotytube'
callback_url = 'https://' + app_id + '.appspot.com/oauth_callback'

# Consumer Api Keys Spotify
consumer_key = 'cb169bdfb3884a03ba9c68932f87285b'
consumer_secret = '5ad8b30856c64e569685769261fa2689'

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

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()


config = {'webapp2_extras.sessions': {'secret_key': 'my-super-secret-key'}}

prefix = 'https://api.spotify.com/v1/'


class MainHandler(BaseHandler):

    def get(self):
        logging.debug('ENTERING MainHandler --->')

        oauth_token = self.session.get('oauth_token')

        if oauth_token is None:
            # Si no hay token
            self.redirect('/LoginAndAuthorize')

        template_values = {'oauth_token': oauth_token}
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


# Spotify
class LoginAndAuthorizeHandler(BaseHandler):
    token_info = None

    def get(self):
        logging.debug('ENTERING LoginAndAuthorizeHandler --->')

        # Step 1: Obtaining a request token
        token_info = self._get_access_token()
        token_info_json = json.dumps(token_info)

        # and store  values
        self.session['oauth_token'] = str(token_info_json).replace('"', '')
        # volver a index
        self.redirect('/')

    def _get_access_token(self):
        if self.token_info and not self.is_token_expired(self.token_info):
            return self.token_info['access_token']

        token_info = self._request_token()
        token_info = self._add_custom_values_to_token_info(token_info)
        self.token_info = token_info

        return self.token_info['access_token']

    @staticmethod
    def _request_token():
        authorization = base64.standard_b64encode(consumer_key + ':' + consumer_secret)

        headers = {'User-Agent': 'Google App Engine',
                   'Authorization': 'Basic {0}'.format(authorization)}
        data = {'grant_type': 'client_credentials'}

        oauth_token_url = 'https://accounts.spotify.com/api/token'

        response = requests.post(oauth_token_url, headers=headers, data=data)

        if response.status_code != 200:
            print response.reason
        token_info = response.json()
        return token_info

    def _add_custom_values_to_token_info(self, token_info):
        token_info['expires_at'] = int(time.time()) + token_info['expires_in']
        return token_info

    def is_token_expired(self, token_info):
        now = int(time.time())
        return token_info['expires_at'] - now < 60


class LoginAndAuthorizeGoogleHandler(BaseHandler):
    google_secret_key = "1FfMRgteyw6T8b46872U0dgb"
    client_id = "990115409802-q9o1n9f5hab5lrlg84l21u2si23m90ph.apps.googleusercontent.com"

    def get(self):
        # Enviar una solicitud de autenticacion a google
        self._authentication_request()
        # Verify token
        # secretjson = self._verify_token(token)


    def _verify_token(self, token):
        params = {'id_token': token}
        response = requests.get("https://oauth2.googleapis.com/tokeninfo?", params=params)
        return response.content

    def _authentication_request(self):
        redirect_uri = 'http://localhost:8080/oauth2callback' #Localhost
        #redirect_uri = 'http://spotytube.appspot.com/oauth2callback'

        server = 'https://accounts.google.com/o/oauth2/v2/auth'

        params = {'client_id': self.client_id,
                  'response_type': 'code',
                  'scope': 'https://www.googleapis.com/auth/youtube',
                  'redirect_uri': redirect_uri}

        headers = {'User-Agent': 'Google App Engine'}

        params_encoded = urllib.urlencode(params)

        response = requests.get(server, headers=headers, params=params_encoded)
        if response.status_code == 200:
            self.redirect(str(response.url))



class SearchSpotify(BaseHandler):
    def get(self):
        logging.debug('ENTERING SearchSpotify --->')
        self.oauth_token = self.session['oauth_token']

        to_search = self.request.get("search")
        result = self.search(to_search)
        # id del artista
        print (result['tracks']['items'][0]['artists'][0]['id'])

    def _request(self, url, data):
        if not url.startswith('http'):
            url = prefix + url
        headers = {'Authorization': 'Bearer {0}'.format(self.oauth_token), 'Content-Type': 'application/json'}

        respuesta = requests.get(url, headers=headers, **data)
        if respuesta.text and len(respuesta.text) > 0 and respuesta.text != 'null':
            results = respuesta.json()
            print()
            return results
        else:
            return None

    def _get(self, url, **kwargs):
        return self._request(url, kwargs)

    def search(self, query, limit=10, offset=0, type='track', market=None):
        return self._get('search', q=query, limit=limit, offset=offset, type=type, market=market)

class OauthCallBackHandler(BaseHandler):
    def get(self):
        # Get code
        code = self.request.get('code')

        # Get token
        headers={'Content-Type': 'application/x-www-form-urlencoded',
                 'User-Agent': 'Google App Engine'}
        response = requests.post("www.googleapis.com/oauth2/v4/token")

        print code

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/LoginAndAuthorize', LoginAndAuthorizeHandler),
    ('/LoginGoogle', LoginAndAuthorizeGoogleHandler),
    ('/oauth2callback', OauthCallBackHandler),
    ('/SearchSpotify', SearchSpotify)

], config=config, debug=True)
