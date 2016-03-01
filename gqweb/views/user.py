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

from collections import defaultdict


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


@app.route('/user/gedit/<u>')
@admin_permission.require(403)
def user_group_view(u):
    user = User.query.filter_by(name=u).first()
    tree = build_group_tree_db(Group.query.all())
    children = defaultdict(list)
    user_groups = set(x.group_name for x in user.groups)
    available = set()

    for group in tree.breadth_first():
        if getattr(group, 'visited', False):
            continue
        group.visited = True
        if group.full_name in user_groups:
            for child in group:
                child.visited = True
        else:
            available.add(group.full_name)

    app.logger.info(available)
    can_add = []

    # for group in tree:
    #     for ug in user_groups:
    #         if group.full_name.startswith(ug) and ug != group.full_name:
    #             children[ug].append(group.full_name)
    #
    # can_add = [x.full_name for x in tree if not any(x.full_name.startswith(y) for y in user_groups)]
    # app.logger.info("%s :::: %s", children, can_add)

    return render_template('user_groupedit.html', u=user, groups=tree, children=children, avail=can_add)


@app.route('/user/gedit/<u>', methods=['POST'])
@admin_permission.require(403)
def user_group_edit(u):
    user = User.query.filter_by(name=u).first()
    return render_template('user_groupedit.html', u=user)
