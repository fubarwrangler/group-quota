# ===========================================================================
# Methods alter users and their permissions
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import request, render_template, redirect, url_for, flash, Response  # flake8: noqa TODO: REMOVE ME

from .. import app

from ..db import db_session
from ..db.models import User, Role


@app.route('/user/add', methods=['POST'])
def add_user():

    user = request.form.get('username')
    comment = request.form.get('comment')
    active = bool(request.form.get('active', False))

    if user is None:
        flash('Required fields for new user: username')
        return redirect(url_for('usermanager'))

    if User.query.filter(User.name == user).first():
        flash('Cannot add: user %s already exists' % user, category='tmperror')
        return redirect(url_for('usermanager'))

    db_session.add(User(name=user, comment=comment, active=active))
    db_session.commit()

    flash('Added new user %s' % user)

    return redirect(url_for('usermanager'))

@app.route('/user/api/remove', methods=['POST'])
def remove_user():

    # TODO: Block removing current user

    data = request.get_json()
    user = data['user']
    User.query.filter_by(name=user).delete()
    db_session.commit()
    return Response(status=204)

@app.route('/user/api/rolechange', methods=['POST'])
def change_role():

    data = request.get_json()

    username = data['user']
    role = data['role']
    action = data['action']

    user = User.query.filter_by(name=username).first()
    therole = Role.query.filter_by(name=role).first()

    if not user or not role:
        return Response(status=520)

    if action:
        user.roles.append(therole)
    else:
        user.roles.remove(therole)

    db_session.commit()

    return Response(status=204)

@app.route('/user/api/activate', methods=['POST'])
def activeate_user():

    # TODO: Block deactivating current user

    data = request.get_json()
    username = data['user']
    user = User.query.filter_by(name=username).first()
    if not user:
        return Response(status=520)

    user.active = data['active'] == 'on'

    db_session.commit()
    return Response(status=200)
