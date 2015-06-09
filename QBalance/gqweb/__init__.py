
from flask import Flask, request, render_template, redirect, url_for, make_response

from flask.ext.wtf import Form
from wtforms import TextField, SubmitField
from wtforms.validators import DataRequired


SQLALCHEMY_DATABASE_URI = 'mysql://willsk@localhost/group_quotas'

app = Flask(__name__)

app.config.from_object(__name__)
app.config.from_envvar('CCFGDIST_CFG', silent=True)
app.config['APPLICATION_ROOT'] = '/farmapp/'

import models

a = models.Group('foo')

# if __name__ == '__main__':
#     app.run(debug=True)
