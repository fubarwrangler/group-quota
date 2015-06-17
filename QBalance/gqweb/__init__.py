
from collections import defaultdict

from flask import (Flask, request, render_template, redirect, url_for,
                   flash)

app = Flask(__name__)

app.config.from_object(__name__)
app.config.from_object('gqweb.default_settings')
app.config.from_envvar('GQEDITCFG', silent=True)
# app.config['APPLICATION_ROOT'] = '/farmapp/'

import quota_edit as qe
from database import db_session
from models import Group, build_group_tree_db


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def main_menu():
    root = build_group_tree_db(Group.query.all())
    return render_template('group_view.html', groups=reversed(list(root)))


@app.route('/edit')
def edit_groups():

    root = build_group_tree_db(Group.query.all())

    return render_template('edit_group.html', groups=reversed(list(root)))


@app.route('/edit', methods=['POST'])
def edit_groups_form():
    data = defaultdict(dict)
    for k, value in request.form.iteritems():
        group, parameter = k.split('+')
        data[group][parameter] = value

    errors = list()
    for grpname in data:
        data[grpname], e = qe.validate_form_types(data[grpname])
        errors.extend(e)

    if errors:
        return render_template('edit_error.html', errors=errors)

    db_groups = Group.query.all()

    qe.set_params(db_groups, data)

    root = build_group_tree_db(db_groups)

    qe.set_quota_sums(db_groups, root)

    db_session.commit()
    flash("Everything OK, changes committed!")
    return redirect(url_for('main_menu'))


@app.route('/add', methods=['GET', 'POST'])
def add_groups():
    return "Add group"