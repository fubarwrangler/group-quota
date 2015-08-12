# ===========================================================================
# Methods alter users and their permissions
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import request, redirect, url_for, flash, Response, session, g

from ..application import app

from ..db import db_session
from ..db.models import User, Role
from ..util.userload import admin_permission


Ok = lambda x: Response(status=200, response=x)
OkNoResponse = lambda: Response(status=204)
Error = lambda x: Response(status=520, response=x)


@app.route('/user/add', methods=['POST'])
@admin_permission.require(403)
def add_user():

    user = request.form.get('username')
    comment = request.form.get('comment')
    active = bool(request.form.get('active', False))

    if not user:
        flash('Required fields for new user: username')
        return redirect(url_for('usermanager'))

    if User.query.filter(User.name == user).first():
        flash('Cannot add: user %s already exists' % user, category='tmperror')
        return redirect(url_for('usermanager'))

    uobj = User(name=user, comment=comment, active=active)
    uobj.roles = list()

    db_session.add(uobj)
    db_session.commit()

    flash('Added new user %s' % user)

    return redirect(url_for('usermanager'))


@app.route('/user/api/remove', methods=['POST'])
@admin_permission.require(403)
def remove_user():

    data = request.json
    user = data['user']
    if g.user == user:
        return Error("Cannot remove own user!")

    User.query.filter_by(name=user).delete()
    db_session.commit()
    return Ok("Removed user " + user)


@app.route('/user/api/rolechange', methods=['POST'])
@admin_permission.require(403)
def change_role():

    data = request.json

    username = data['user']
    role = data['role']
    action = data['action']

    user = User.query.filter_by(name=username).first()
    therole = Role.query.filter_by(name=role).first()

    # Block removing current user & neutering the admin
    if not user or not role:
        return Error("User %s or role %s not found" % (user, therole))
    elif role == 'admin' and username == g.user:
        return Error("Can't remove admin from yourself!")

    if action:
        user.roles.append(therole)
        msg = "Added role <b>{0}</b> to user <i>{1}</i>"
    else:
        user.roles.remove(therole)
        msg = "Removed role <b>{0}</b> from user <i>{1}</i>"

    db_session.commit()
    session['reload_roles'] = True

    return Ok(msg.format(role, username))


@app.route('/user/api/activate', methods=['POST'])
@admin_permission.require(403)
def activeate_user():

    data = request.json
    username = data['user']
    user = User.query.filter_by(name=username).first()

    if not user:
        return Error("User " + username + " not found!")

    user.active = data['active'] == 'on'

    # Block deactivating current user
    if username == g.user and not user.active:
        return Error("Cannot deactivate yourself!")

    session['reload_roles'] = True

    db_session.commit()
    return OkNoResponse()
