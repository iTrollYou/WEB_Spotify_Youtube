#!/usr/bin/env python
import time

import logging
import os

import base64
import json
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
        template_values = {'oauth_token': oauth_token}

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class LoginAndAuthorizeHandler(BaseHandler):
    token_info = None

    def get(self):
        logging.debug('ENTERING LoginAndAuthorizeHandler --->')

        # Step 1: Obtaining a request token
        token_info = self._get_access_token()
        token_info_json = json.dumps(token_info)
        # and store  values
        self.session['oauth_token'] = token_info_json

    def _get_access_token(self):
        if self.token_info and not self.is_token_expired(self.token_info):
            return self.token_info['access_token']

        token_info = self._request_token()
        token_info = self._add_custom_values_to_token_info(token_info)
        self.token_info = token_info

        return self.token_info['access_token']

    def _request_token(self):
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
        print token_info
        token_info['expires_at'] = int(time.time()) + token_info['expires_in']
        return token_info

    def is_token_expired(self, token_info):
        now = int(time.time())
        return token_info['expires_at'] - now < 60


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/LoginAndAuthorize', LoginAndAuthorizeHandler)

], config=config, debug=True)
