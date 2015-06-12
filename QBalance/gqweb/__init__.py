
from collections import defaultdict

from flask import Flask, request, render_template, redirect, url_for, make_response

from flask.ext.wtf import Form
from wtforms import TextField, SubmitField
from wtforms.validators import DataRequired


SQLALCHEMY_DATABASE_URI = 'mysql://willsk@localhost/group_quotas'

app = Flask(__name__)

app.config.from_object(__name__)
app.config.from_envvar('CCFGDIST_CFG', silent=True)
app.config['APPLICATION_ROOT'] = '/farmapp/'

from database import db_session
from models import Group, build_group_tree


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def show_menu():
    root = build_group_tree(Group.query.all())
    return render_template('group_view.html', groups=root)


@app.route('/edit')
def edit_groups():

    root = build_group_tree(Group.query.all())

    return render_template('edit_group.html', groups=reversed(list(root)))


@app.route('/edit', methods=['POST'])
def edit_groups_form():
    app.logger.debug(request.form)
    data = defaultdict(dict)
    for k, value in request.form.iteritems():
        group, parameter = k.split('+')
        data[group][parameter] = value

    for grpname in data:
        group = Group.query.filter_by(group_name=grpname).first()
        for param, val in data[grpname].iteritems():
            oldval = getattr(group, param)
            if oldval != val:
                app.logger.warning("Changing val: %s [%s] %s->%s", grpname, param, oldval, val)
                setattr(group, param, val)

    db_session.commit()

    return "Database updated"
