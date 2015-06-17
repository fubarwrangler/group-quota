
from flask import Flask, render_template

app = Flask(__name__)

app.config.from_object(__name__)
app.config.from_object('gqweb.default_settings')
app.config.from_envvar('GQEDITCFG', silent=True)
# app.config['APPLICATION_ROOT'] = '/farmapp/'

from database import db_session
from models import Group, build_group_tree_db

import quota_edit  # flake8: noqa -- this unused import has views


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def main_menu():
    root = build_group_tree_db(Group.query.all())
    return render_template('main_view.html', groups=sorted(list(root), key=lambda x: x.full_name))


@app.route('/edit')
def edit_groups():
    root = build_group_tree_db(Group.query.all())
    return render_template('edit_group.html', groups=sorted(list(root), key=lambda x: x.full_name))


@app.route('/addrm')
def add_groups():
    root = build_group_tree_db(Group.query.all())
    return render_template('group_add_rm.html', groups=sorted(list(root), key=lambda x: x.full_name))
