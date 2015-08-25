# ===========================================================================
# Application to allow users to modify the group-quota tree used by ATLAS
#   Allows different classes of users to modify group quotas and parameters
#   and the tree itself in the database
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import (Flask, render_template, flash, redirect, url_for, config,
                   request, session)
from flask.ext.principal import Principal
import logging

app = Flask(__name__)

principals = Principal(app)

app.config.from_object(__name__)
app.config.from_object('gqweb.default_settings')
app.config.from_envvar('GQEDITCFG', silent=True)

from db import db_session
from db.models import Group, User, Role, build_group_tree_db
from util.validation import group_defaults
from util.app_logging import log_setup
from util.userload import (admin_permission, edit_permission, balance_permission,
                           add_remove_permission)


import views.quota_edit       # flake8: noqa -- this unused import has views
import views.group_modify     # flake8: noqa -- this unused import has views
import views.ez_edit          # flake8: noqa -- this unused import has views
import views.user             # flake8: noqa -- this unused import has views
import views.plot_idle        # flake8: noqa -- this unused import has setup
import views.pre_initialize   # flake8: noqa -- this unused import has setup

if app.config.get('LOG_FILE'):
    log_setup(app.config.get('LOG_FILE'), app.config.get('LOG_LEVEL', logging.INFO))

namesort = lambda root: sorted(list(root), key=lambda x: x.full_name)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/logout')
def logout():
    url = request.values.get('target')
    if 'user' in session: session.pop('user')
    if 'roles' in session: session.pop('roles')
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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def page_not_found(e):
    return render_template('errors/403.html'), 403
