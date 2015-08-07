# ===========================================================================
# Application to allow users to modify the group-quota tree used by ATLAS
#   Allows different classes of users to modify group quotas and parameters
#   and the tree itself in the database
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import (Flask, render_template, flash, redirect, url_for, config,
                   request, session, g)
from flask.ext.principal import Principal, Identity, AnonymousIdentity, RoleNeed

app = Flask(__name__)

principals = Principal(app)

app.config.from_object(__name__)
app.config.from_object('gqweb.default_settings')
app.config.from_envvar('GQEDITCFG', silent=True)
# app.config['APPLICATION_ROOT'] = '/farmapp/'

from db import db_session
from db.models import Group, User, Role, build_group_tree_db
from util.validation import group_defaults
from util.userload import load_user_debug, load_user_header
from util.userload import (admin_permission, edit_permission, balance_permission,
                           add_remove_permission)


import views.quota_edit       # flake8: noqa -- this unused import has views
import views.group_modify     # flake8: noqa -- this unused import has views
import views.ez_edit          # flake8: noqa -- this unused import has views
import views.user          # flake8: noqa -- this unused import has views


namesort = lambda root: sorted(list(root), key=lambda x: x.full_name)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.before_first_request
def default_users_and_roles():

    def add_unique(obj, attr='name'):
        ocl = type(obj)
        if not ocl.query.filter(getattr(ocl, attr) == getattr(obj, attr)).first():
            db_session.add(obj)

    add_unique(User(name=app.config['ADMIN_USER'], active=True, comment="Default admin user"))

    add_unique(Role(name='admin',   comment='Full administrator with all privileges'))
    add_unique(Role(name='alter',   comment='Can add / remove groups'))
    add_unique(Role(name='edit',    comment='Can edit all group parameters'))
    add_unique(Role(name='balance', comment='Can rebalance quotas with EZ-Editor'))

    db_session.commit()


@principals.identity_loader
def load_identity():
    if request.path.startswith("/static/"):
        return AnonymousIdentity()

    reconfig = session.get('reload_roles', False)
    if reconfig:
        session.pop('reload_roles')
    username = session.get('user')
    if not username or reconfig:
        app.logger.info("New user loaded")

        if app.config['DEBUG']:
            username = load_user_debug(app.config['ADMIN_USER'])
        else:
            username = load_user_header('REMOTE_USER')
        session['user'] = username

    roles = session.get('roles')
    if not roles or reconfig:
        user = User.query.filter_by(name=username).first()
        if not user or not user.active:
            return AnonymousIdentity()
        roles = [role.name for role in user.roles]
        app.logger.info("New roles loaded: %s", roles)
        session['roles'] = roles

    identity = Identity(username)
    for role in roles:
        identity.provides.add(RoleNeed(role))

    g.user = username
    g.roles = roles

    return identity

@app.route('/logout')
def logout():
    url = request.values.get('target')
    session.pop('user')
    session.pop('roles')
    return redirect(url)


@app.route('/')
def main_menu():
    root = build_group_tree_db(Group.query.all())
    return render_template('main_view.html', groups=namesort(root))


@app.route('/edit')
@edit_permission.require(403)
def edit_groups():
    root = build_group_tree_db(Group.query.all())
    return render_template('edit_group.html', groups=namesort(root))


@app.route('/addrm')
@add_remove_permission.require(403)
def add_groups():
    root = build_group_tree_db(Group.query.all())
    return render_template('group_add_rm.html', groups=namesort(root),
                           defaults=group_defaults)

@app.route('/ezq')
@balance_permission.require(403)
def ez_quota_chooser():
    root = build_group_tree_db(Group.query.all())
    return render_template('quota_group_chooser.html', groups=namesort(root))


@app.route('/ezq/<parent>')
def ez_quota_edit(parent):

     # NOTE: Could narrow the db-query down some but this is easiest for now
    group = build_group_tree_db(Group.query.all()).find(parent)

    if not group or not group.children or len(group.children) <= 1:
        flash('Group %s not an intermediate group with >1 children!' % parent, category="error")
        return redirect(url_for('main_menu'))

    subtree = group.children.values()

    # Special case for root node, set it's quota here -- must be a better way!
    if group.parent is None:
        group.quota = sum(x.quota for x in subtree)

    return render_template('quota_edit.html', groups=subtree)


@app.route('/user')
@admin_permission.require(403)
def usermanager():
    return render_template('user.html', u=User.query.all(),
                           r=Role.query.all())
