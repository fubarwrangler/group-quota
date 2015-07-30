# ===========================================================================
# Methods to validate edited quota info from form data and make changes
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import request, render_template, redirect, url_for, flash  # flake8: noqa TODO: REMOVE ME

from .. import app

from ..db import db_session
from ..db.models import User, Role


@app.before_first_request
def default_users_and_roles():
    username = app.config['DEFAULT_USER']
    rolename = app.config['DEFAULT_USER_ROLE']
    if not User.query.filter(User.name==username).count():
        db_session.add(User(name=username, active=True))
    if not Role.query.filter(Role.name==rolename).count():
        db_session.add(Role(name=rolename))
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
