# ===========================================================================
# Methods alter users and their permissions
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import request, redirect, url_for, flash, Response, session

from .. import app

from ..db import db_session
from ..db.models import User, Role
from ..util.userload import admin_permission


@app.route('/user/add', methods=['POST'])
@admin_permission.require(403)
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
@admin_permission.require(403)
def remove_user():

    # TODO: Block removing current user

    data = request.get_json()
    user = data['user']
    User.query.filter_by(name=user).delete()
    db_session.commit()
    return Response(status=204)


@app.route('/user/api/rolechange', methods=['POST'])
@admin_permission.require(403)
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
    session['reload_roles'] = True

    return Response(status=204)


@app.route('/user/api/activate', methods=['POST'])
@admin_permission.require(403)
def activeate_user():

    # TODO: Block deactivating current user

    data = request.get_json()
    username = data['user']
    user = User.query.filter_by(name=username).first()
    if not user:
        return Response(status=520)

    user.active = data['active'] == 'on'
    session['reload_roles'] = True

    db_session.commit()
    return Response(status=200)
