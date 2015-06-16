
from collections import defaultdict

from flask import (Flask, request, render_template, redirect, url_for,
                   flash)

app = Flask(__name__)

app.config.from_object(__name__)
app.config.from_envvar('GQEDITCFG', silent=True)
# app.config['APPLICATION_ROOT'] = '/farmapp/'

# XXX: NOT REALLY USED IN PROD: Do the following and put in environs
#
#   $ tr -c -d '[:alnum:][!#$%&*.,]' < /dev/urandom | head -c 20
#
app.secret_key = 'U.iQ4!%&qvn$OzFrmBkz'

from database import db_session
from models import Group, build_group_tree_db, type_map


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def main_menu():
    root = build_group_tree_db(Group.query.all())
    return render_template('group_view.html', groups=root)


@app.route('/edit')
def edit_groups():

    root = build_group_tree_db(Group.query.all())

    return render_template('edit_group.html', groups=reversed(list(root)))


def validate_form_types(data):
    errors = list()
    for k, v in data.items():
        fn, valid, msg = type_map[k]
        try:
            data[k] = fn(v)
            if not valid(data[k]):
                raise ValueError
        except ValueError:
            errors.append((data['group_name'], k, msg))

    return data, errors


@app.route('/edit', methods=['POST'])
def edit_groups_form():
    data = defaultdict(dict)
    for k, value in request.form.iteritems():
        group, parameter = k.split('+')
        data[group][parameter] = value

    errors = []
    for grpname in data:
        data[grpname], e = validate_form_types(data[grpname])
        errors.extend(e)

    if errors:
        return render_template('edit_error.html', errors=errors)

    root = build_group_tree_db(Group.query.all())
    for name, params in data.iteritems():
        dbobj = next(x for x in root if x.full_name == name)
        for param, val in params.iteritems():
            if param == 'group_name':
                continue
            db_val = getattr(dbobj, param)
            if db_val != val:
                app.logger.info("%s <> %s -- my: %s, db: %s",
                                name, param, val, db_val)
                setattr(dbobj, param, val)

            old = dbobj.quota
            new = sum(x.quota for x in dbobj.get_children())
            app.logger.info("Intermediate group sum %s: %d->%d", dbobj.full_name, old, new)

            # FIXME: and not user_sum_change_auth
            if new != old and True:
                dbobj.quota = new

    db_session.commit()
    flash("Everything OK, changes committed!")
    return redirect(url_for('main_menu'))
