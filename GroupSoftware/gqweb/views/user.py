# ===========================================================================
# Methods to validate edited quota info from form data and make changes
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import request, render_template, redirect, url_for, flash  # flake8: noqa TODO: REMOVE ME

from .. import app

from ..db import db_session
from ..db.models import User, Role


def add_unique(obj, attr='name'):
    if not type(obj).query.filter(getattr(type(obj), attr) == getattr(obj, attr)).count():
        db_session.add(obj)


@app.before_first_request
def default_users_and_roles():

    add_unique(User(name=app.config['DEFAULT_USER'], active=True, comment="Default admin user"))
    add_unique(Role(name='admin', comment='Full administrator with all privileges'))
    add_unique(Role(name='alter', comment='Can add / remove groups as well as edit them'))
    add_unique(Role(name='edit', comment='Can edit anything about existing groups'))

    db_session.commit()


@app.route('/user/add', methods=['POST'])
def add_user():

    userdata = request.form.iteritems()
    db_session.commit()

    return redirect(url_for('main_menu'))


@app.route('/user/remove', methods=['POST'])
def remove_user():

    userdata = request.form.iteritems()
    db_session.commit()

    return redirect(url_for('main_menu'))
