# ===========================================================================
# Application to allow users to modify the group-quota tree used by ATLAS
#   Allows different classes of users to modify group quotas and parameters
#   and the tree itself in the database
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import Flask, render_template

app = Flask(__name__)

app.config.from_object(__name__)
app.config.from_object('gqweb.default_settings')
app.config.from_envvar('GQEDITCFG', silent=True)
# app.config['APPLICATION_ROOT'] = '/farmapp/'

from database import db_session
from models import Group, build_group_tree_db

import quota_edit       # flake8: noqa -- this unused import has views
import group_modify     # flake8: noqa -- this unused import has views


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
def ez_quota_edit():
    root = build_group_tree_db(Group.query.all())
    return render_template('quota_edit.html', groups=namesort(root))
