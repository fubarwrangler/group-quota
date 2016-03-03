# ===========================================================================
# Methods alter users and their permissions
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import (request, redirect, url_for, flash, render_template,
                   Response, session, g)

from ..application import app

from ..db import db_session
from ..db.models import User, Role, Group, build_group_tree_db
from ..util.userload import admin_permission
from ..util.tree import valid_exclusion_tree


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

    msg = 'Added new user %s' % user
    app.logger.info(msg)
    flash(msg)

    return redirect(url_for('usermanager'))


@app.route('/user/api/remove', methods=['POST'])
@admin_permission.require(403)
def remove_user():

    data = request.get_json()
    user = data['user']
    if g.user == user:
        return Error("Cannot remove own user!")

    User.query.filter_by(name=user).delete()
    db_session.commit()

    app.logger.info("Removed user %s", user)

    return Ok("Removed user " + user)


@app.route('/user/api/rolechange', methods=['POST'])
@admin_permission.require(403)
def change_role():

    data = request.get_json()

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

    app.logger.info(msg.format(role, username))

    return Ok(msg.format(role, username))


@app.route('/user/api/activate', methods=['POST'])
@admin_permission.require(403)
def activate_user():

    data = request.get_json()
    username = data['user']
    user = User.query.filter_by(name=username).first()

    if not user:
        return Error("User " + username + " not found!")

    user.active = data['active'] == 'on'

    # Block deactivating current user
    if username == g.user and not user.active:
        return Error("Cannot deactivate yourself!")

    session['reload_roles'] = True

    app.logger.info("%sctivated user %s", 'A' if user.active else 'Dea', username)

    db_session.commit()
    return OkNoResponse()


@app.route('/user/gedit/<uid>', methods=['POST'])
@admin_permission.require(403)
def user_group_edit(uid):
    user = User.query.filter_by(id=uid).first()
    new_groups = set(request.form.getlist('ng'))
    app.logger.info("Changed groups for %s: %s", user.name, new_groups)

    root = build_group_tree_db(Group.query.all())
    if not valid_exclusion_tree(new_groups, root):
        flash("New grouplist contains a child of one of itself", category='error')
        return redirect(url_for('user_group_view', uid=uid))

    user.groups = Group.query.filter(Group.group_name.in_(new_groups)).all()
    db_session.commit()
    flash("Success changing allowed groups for %s" % user)

    return redirect(url_for('usermanager'))
