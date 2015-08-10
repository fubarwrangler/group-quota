#!/usr/bin/python
import logging
from gqweb import app
from werkzeug.serving import run_simple

URL_PREFIX = '/farmdebug'


class ScriptNameEdit(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        url = environ['SCRIPT_NAME']
        environ['SCRIPT_NAME'] = URL_PREFIX + url
        return self.app(environ, start_response)


app = ScriptNameEdit(app)

if __name__ == '__main__':
    run_simple('0.0.0.0', 5000, app,
               use_reloader=True, use_debugger=True, use_evalex=True)
