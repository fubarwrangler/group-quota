# ===========================================================================
# Methods alter users and their permissions
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import request, render_template, redirect, url_for, flash  # flake8: noqa TODO: REMOVE ME

from .. import app

from ..db import db_session
from ..db.models import User, Role


def add_unique(obj, attr='name'):
    if not type(obj).query.filter(getattr(type(obj), attr) == getattr(obj, attr)).first():
        db_session.add(obj)


@app.before_first_request
def default_users_and_roles():

    add_unique(User(name=app.config['ADMIN_USER'], active=True, comment="Default admin user"))

    add_unique(Role(name='admin',   comment='Full administrator with all privileges'))
    add_unique(Role(name='alter',   comment='Can add / remove groups'))
    add_unique(Role(name='edit',    comment='Can edit all group parameters'))
    add_unique(Role(name='balance', comment='Can rebalance quotas with EZ-Editor'))
    add_unique(Role(name='anon',    comment='Read-only, no privileges to alter'))

    db_session.commit()


@app.route('/user/add', methods=['POST'])
def add_user():

    user = request.form.get('username')
    comment = request.form.get('comment')
    active = bool(request.form.get('active', False))

    if user is None:
        flash('Required fields for new user: username')
        return redirect(url_for('usermanager'))

    if User.query.filter(User.name == user).first():
        flash('Cannot add: user %s already exists' % user)
        return redirect(url_for('usermanager'))

    db_session.add(User(name=user, comment=comment, active=active))
    db_session.commit()

    return redirect(url_for('usermanager'))


@app.route('/user/remove', methods=['POST'])
def remove_user():

    uid = request.form.get('userid')
    app.logger.info("Remove %s", uid)
    User.query.get(uid).delete()
    db_session.commit()

    return redirect(url_for('usermanager'))

@app.route('/user/api/<username>/rolechange', methods=['POST'])
def change_role(username):

    data = request.get_json()
    app.logger.info(data)

    role = data['role']
    change = data['action'].lower()

    user = User.query.filter(User.name == username).first()
    therole = User.query.filter(Role.name == role).first()

    if not user or not role:
        flash('API Error: no user+role %s + %s found' % (username, role))
        return redirect(url_for('usermanager'))

    if change == 'add':
        user.roles.append(therole)
        flash('Role %s added to user %s' % (role, username))
    else:
        user.roles.remove(therole)
        flash('Role %s removed to user %s' % (role, username))

    db_session.commit()
    return render_template('user.html')

@app.route('/user/api/<username>/activate', methods=['POST'])
def activeate_user(username):

    data = request.get_json()

    user = User.query.filter(User.name == username).first()

    if not user or not role:
        flash('API Error: no user %s found' % username)
        return redirect(url_for('usermanager'))

    user.active = data['active']

    db_session.commit()
    return render_template('user.html')
