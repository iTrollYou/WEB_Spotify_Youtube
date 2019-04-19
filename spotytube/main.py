import urllib
import json
from webapp2_extras import sessions
import webapp2
import logging

# Use Requests in GAE
import requests
import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()

# Identificador de la App en GAE
gae_app_id = 'spotytube'

# La callBack URI debe estar definida en la App de DROPBOX
# https://www.dropbox.com/developers/apps
gae_callback_url = 'https://' + gae_app_id + '.appspot.com/oauth_callback'

# Api key y Api secret en dropbox
dropbox_app_key = '2q24sjqorfg66ek'
dropbox_app_secret = 't19789pyf829yre'


# SESIONES
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


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('<html><head>')
        self.response.write('<title>LoginAndAuthorize</title>')
        self.response.write('</head>')
        self.response.write('<body>')
        self.response.write('<a href="/LoginAndAuthorize">Login and Authorize with Dropbox</a>')
        self.response.write('</body></html>')


class LoginAndAuthorize(webapp2.RequestHandler):
    def get(self):
        url = 'https://www.dropbox.com/1/oauth2/authorize'
        parametros = {'response_type': 'code',
                      'client_id': dropbox_app_key,  # App key
                      'redirect_uri': gae_callback_url}

        parametros = urllib.urlencode(parametros)
        self.redirect(url + '?' + parametros)


class OAuthHandler(BaseHandler):
    def get(self):
        request_url = self.request.url
        code = request_url.split('code=')[1]
        url = 'https://api.dropbox.com/1/oauth2/token'
        parametros = {'code': code,
                      'grant_type': 'authorization_code',
                      'client_id': dropbox_app_key,  # App key
                      'client_secret': dropbox_app_secret,  # App secret
                      'redirect_uri': gae_callback_url}

        cabeceras = {'Content-Type': 'application/x-www-form-urlencoded', }

        respuesta = requests.post(url, headers=cabeceras, data=parametros)

        json_contenido = json.loads(respuesta.content)

        self.session['access_token'] = json_contenido['access_token']

        self.redirect('/CreateFile')


class CreateFile(BaseHandler):
    def get(self):
        access_token = self.session['access_token']

        path = '/fichero.txt'
        url = 'https://content.dropboxapi.com/2/files/upload'
        parametros = {'path': path}

        parametros = json.dumps(parametros)

        cuerpo = 'Este es el contenido del fichero.'
        cabeceras = {'Authorization': 'Bearer ' + access_token,
                     'DropBox-API-Arg': parametros,
                     'Content-Type': 'application/octet-stream', }

        respuesta = requests.post(url, headers=cabeceras, data=cuerpo)

        self.response.write('<p>Asegurate que se ha generado el fichero en DropBox</p>')
        self.response.write(respuesta.content)


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/LoginAndAuthorize', LoginAndAuthorize),
    ('/oauth_callback', OAuthHandler),
    ('/CreateFile', CreateFile)
], config=config, debug=True)
