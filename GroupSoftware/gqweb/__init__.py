# ===========================================================================
# Application to allow users to modify the group-quota tree used by ATLAS
#   Allows different classes of users to modify group quotas and parameters
#   and the tree itself in the database
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import Flask, render_template, flash, redirect, url_for, config

app = Flask(__name__)

app.config.from_object(__name__)
app.config.from_object('gqweb.default_settings')
app.config.from_envvar('GQEDITCFG', silent=True)
# app.config['APPLICATION_ROOT'] = '/farmapp/'

from db import db_session
from db.models import Group, build_group_tree_db

import views.quota_edit       # flake8: noqa -- this unused import has views
import views.group_modify     # flake8: noqa -- this unused import has views
import views.ez_edit          # flake8: noqa -- this unused import has views


namesort = lambda root: sorted(list(root), key=lambda x: x.full_name)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def main_menu():
    root = build_group_tree_db(Group.query.all())
    return render_template('main_view.html', groups=namesort(root))


@app.route('/edit')
def edit_groups():
    root = build_group_tree_db(Group.query.all())
    return render_template('edit_group.html', groups=namesort(root))


@app.route('/addrm')
def add_groups():
    root = build_group_tree_db(Group.query.all())
    return render_template('group_add_rm.html', groups=namesort(root),
                           defaults=group_modify.group_defaults)

@app.route('/ezq')
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
    if subtree[0].parent.parent is None:
        subtree[0].parent.quota = sum(x.quota for x in subtree)

    return render_template('quota_edit.html', groups=subtree)
