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

# Use the App Engine Requests adapter. This makes sure that Requests uses URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()

app_id = 'spotytube'
callback_url = 'https://' + app_id + '.appspot.com/oauth_callback'

# Consumer Api Keys Spotify
consumer_key = 'e5c792dbc36a4ec8a06e0bd91ef111eb'
consumer_secret = '2e88aa2d92df480fb624202f7dd3adf6'

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
        self.session['oauth_token'] = token_info_json
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
        print token_info
        return token_info

    def is_token_expired(self, token_info):
        now = int(time.time())
        return token_info['expires_at'] - now < 60


class LoginAndAuthorizeGoogleHandler(BaseHandler):
    google_secret_key = "1FfMRgteyw6T8b46872U0dgb"
    client_id = "990115409802-q9o1n9f5hab5lrlg84l21u2si23m90ph.apps.googleusercontent.com"

    def get(self):
        # Crear un token de estado anti-falsificación
        state = self._create_state_token()
        # Enviar una solicitud de autenticacion a google
        self._authentication_request(state)

    def _create_state_token(self):
        # Create a state token to prevent request forgery.
        # Store it in the session for later validation.
        state = hashlib.sha256(os.urandom(1024)).hexdigest()
        # Set the client ID, token state, and application name in the HTML while
        # serving it.
        template_values = {'state': state,
                           'client_id': self.client_id,
                           'app_name': app_id}
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        return state

    def _authentication_request(self, state):
        # redirect_uri = 'http://localhost:8080/oauth2callback' #Localhost
        redirect_uri = 'http://spotytube.appspot.com/oauth2callback'

        server = 'https://accounts.google.com/o/oauth2/v2/auth'

        params = {'client_id': self.client_id,
                  'response_type': 'code',
                  'scope': 'openid  andrea98.gar@gmail.com',
                  'nonce': self._generate_nonce(),
                  'redirect_uri': redirect_uri,
                  'state': state}
        headers = {'User-Agent': 'Python Client'}

        params_encoded = urllib.urlencode(params)

        response = requests.get(server, headers=headers, params=params_encoded)

        if response.status_code == 200:
            print 'holi'
            print response.content

    def _generate_nonce(self):
        """Generate pseudorandom number."""
        # return ''.join([str(random.randint(0, 9)) for i in range(length)])
        num1 = [str(random.randint(0, 9)) for i in range(7)]
        num2 = [str(random.randint(0, 9)) for i in range(7)]
        num3 = [str(random.randint(0, 9)) for i in range(7)]
        return ''.join(num1) + '-' + ''.join(num2) + '-' + ''.join(num3)


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/LoginAndAuthorize', LoginAndAuthorizeHandler),
    ('/LoginGoogle', LoginAndAuthorizeGoogleHandler)

], config=config, debug=True)
