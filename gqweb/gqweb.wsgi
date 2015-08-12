#!/usr/bin/python
from gqweb import app as application

URL_PREFIX = '/farmdebug'


class ScriptNameEdit(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        url = environ['SCRIPT_NAME']
        environ['SCRIPT_NAME'] = URL_PREFIX + url
        return self.app(environ, start_response)


class RemoteUserMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        user = environ.get('HTTP_X_MYREMOTE_USER', None)
        environ['REMOTE_USER'] = user
        return self.app(environ, start_response)

application = ScriptNameEdit(application)
application = RemoteUserMiddleware(application)
