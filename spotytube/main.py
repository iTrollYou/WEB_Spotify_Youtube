#!/usr/bin/env python

from webapp2_extras import sessions
import webapp2
import jinja2
import os
import logging
import urllib
import random
import time
import hmac
import binascii
import hashlib

import requests
import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()

app_id = 'spotytube'
callback_url = 'https://' + app_id + '.appspot.com/oauth_callback'

# Consumer Api Keys Spotify
consumer_key = '629b204e06304fb1822837dadd3f5732'
consumer_secret = 'dcfefdac5f3d40f7869805122d151c70'

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


config = {}
config['webapp2_extras.sessions'] = {'secret_key': 'my-super-secret-key'}


class MainHandler(BaseHandler):
    def get(self):
        logging.debug('ENTERING MainHandler --->')
        twitter_user = self.session.get('twitter_user')
        template_values = {'twitter_user': twitter_user}

        template = JINJA_ENVIRONMENT.get_template('jinja2_template.html')
        self.response.write(template.render(template_values))


class LoginAndAuthorizeHandler(BaseHandler):
    def get(self):
        logging.debug('ENTERING LoginAndAuthorizeHandler --->')

        # Step 1: Obtaining a request token
        method = 'POST'
        url = 'https://api.twitter.com/oauth/request_token'
        oauth_headers = {'oauth_callback': callback_url}
        logging.debug(callback_url)

        cabeceras = {'User-Agent': 'Oskarren Google App Engine',
                     'Authorization': createAuthHeader(method, url, oauth_headers, None, None)}
        respuesta = requests.post(url, headers=cabeceras)
        cuerpo = respuesta.text

        # Your application should examine the HTTP status of the response.
        # Any value other than 200 indicates a failure.
        if respuesta.status_code != '200':
            logging.debug('/oauth/request_token != 200')

        # Your application should verify that oauth_callback_confirmed is true
        oauth_callback_confirmed = cuerpo.split('&')[2].replace('oauth_callback_confirmed=', '')
        if oauth_callback_confirmed != 'true':
            logging.debug('oauth_callback_confirmed != true')

        # and store the other two values
        self.session['oauth_token'] = cuerpo.split('&')[0].replace('oauth_token=', '')
        self.session['oauth_token_secret'] = cuerpo.split('&')[1].replace('oauth_token_secret=', '')

        # Step 2: Redirecting the user

        uri = "https://api.twitter.com/oauth/authenticate"
        params = {'oauth_token': self.session.get('oauth_token')}
        params_encoded = urllib.urlencode(params)
        self.redirect(uri + '?' + params_encoded)


class OAuthCallbackHandler(BaseHandler):
    def get(self):
        logging.debug('ENTERING OAuthCallbackHandler --->')

        oauth_token = self.request.get("oauth_token")
        oauth_verifier = self.request.get("oauth_verifier")

        # Your application should verify that the token matches the request token received in step 1
        if oauth_token != self.session.get('oauth_token'):
            logging.debug('step2_oauth_token != step1_oauth_token')

        # Step 3: Converting the request token to an access token
        method = 'POST'
        url = 'https://api.twitter.com/oauth/access_token'
        oauth_headers = {'oauth_token': oauth_token}
        params = {'oauth_verifier': oauth_verifier}

        cabeceras = {'User-Agent': 'Google App Engine',
                     'Content-Type': 'application/x-www-form-urlencoded',
                     'Authorization': createAuthHeader(method, url, oauth_headers, params,
                                                       self.session.get('oauth_token_secret'))}
        respuesta = requests.post(url, headers=cabeceras, data=params)
        cuerpo = respuesta.text

        self.session['oauth_token'] = cuerpo.split('&')[0].replace('oauth_token=', '')
        self.session['oauth_token_secret'] = cuerpo.split('&')[1].replace('oauth_token_secret=', '')
        self.session['user_id'] = cuerpo.split('&')[2].replace('user_id=', '')
        self.session['twitter_user'] = cuerpo.split('&')[3].replace('screen_name=', '')

        self.redirect('/')


class RefreshLast3TweetsHandler(BaseHandler):
    def get(self):
        logging.debug('ENTERING RefreshLast3Tweets --->')
        oauth_token = self.session['oauth_token']
        oauth_token_secret = self.session['oauth_token_secret']

        method = 'GET'
        base_url = 'https://api.twitter.com/1.1/statuses/home_timeline.json'
        oauth_headers = {'oauth_token': oauth_token}
        params = {'count': '3'}
        cabeceras = {'User-Agent': 'Google App Engine',
                     'Authorization': createAuthHeader(method, base_url, oauth_headers, params, oauth_token_secret)}
        params_encoded = urllib.urlencode(params)
        uri = base_url + '?' + params_encoded
        respuesta = requests.get(uri, headers=cabeceras)

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(respuesta.text)


class PublishTweetHandler(BaseHandler):
    def get(self):
        logging.debug('ENTERING PublishTweet --->')
        oauth_token = self.session['oauth_token']
        oauth_token_secret = self.session['oauth_token_secret']

        estatus = self.request.get("tweet")

        method = 'POST'
        base_url = 'https://api.twitter.com/1.1/statuses/update.json'
        oauth_headers = {'oauth_token': oauth_token}
        params = {'status': estatus}
        cabeceras = {'User-Agent': 'Google App Engine',
                     'Content-Type': 'application/x-www-form-urlencoded',
                     'Authorization': createAuthHeader(method, base_url, oauth_headers, params, oauth_token_secret)}
        respuesta = requests.post(base_url, headers=cabeceras, data=params)
        logging.info(respuesta.text)

        self.redirect("/")


def createAuthHeader(method, base_url, oauth_headers, request_params, oauth_token_secret):
    logging.debug('ENTERING createAuthHeader --->')
    oauth_headers.update({'oauth_consumer_key': consumer_key,
                          'oauth_nonce': str(random.randint(0, 999999999)),
                          'oauth_signature_method': "HMAC-SHA1",
                          'oauth_timestamp': str(int(time.time())),
                          'oauth_version': "1.0"})
    oauth_headers['oauth_signature'] = \
        urllib.quote(createRequestSignature(method, base_url, oauth_headers, request_params, oauth_token_secret), "")

    if oauth_headers.has_key('oauth_callback'):
        oauth_headers['oauth_callback'] = urllib.quote_plus(oauth_headers['oauth_callback'])
    authorization_header = "OAuth "
    for each in sorted(oauth_headers.keys()):
        if each == sorted(oauth_headers.keys())[-1]:
            authorization_header = authorization_header \
                                   + each + "=" + "\"" \
                                   + oauth_headers[each] + "\""
        else:
            authorization_header = authorization_header \
                                   + each + "=" + "\"" \
                                   + oauth_headers[each] + "\"" + ", "

    return authorization_header


def createRequestSignature(method, base_url, oauth_headers, request_params, oauth_token_secret):
    logging.debug('ENTERING createRequestSignature --->')
    encoded_params = ''
    params = {}
    params.update(oauth_headers)
    if request_params:
        params.update(request_params)
    for each in sorted(params.keys()):
        key = urllib.quote(each, "")
        value = urllib.quote(params[each], "")
        if each == sorted(params.keys())[-1]:
            encoded_params = encoded_params + key + "=" + value
        else:
            encoded_params = encoded_params + key + "=" + value + "&"

    signature_base = method.upper() + \
                     "&" + urllib.quote(base_url, "") + \
                     "&" + urllib.quote(encoded_params, "")

    if oauth_token_secret == None:
        signing_key = urllib.quote(consumer_secret, "") + "&"
    else:
        signing_key = urllib.quote(consumer_secret, "") + "&" + urllib.quote(oauth_token_secret, "")

    hashed = hmac.new(signing_key, signature_base, hashlib.sha1)
    oauth_signature = binascii.b2a_base64(hashed.digest())

    return oauth_signature[:-1]


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/LoginAndAuthorize', LoginAndAuthorizeHandler),
    ('/oauth_callback', OAuthCallbackHandler),
    ('/RefreshLast3Tweets', RefreshLast3TweetsHandler),
    ('/publishTweet', PublishTweetHandler)

], config=config, debug=True)
