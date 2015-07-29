# ===========================================================================
# Methods to validate edited quota info from form data and make changes
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from collections import defaultdict
from flask import request, render_template, redirect, url_for, flash

from .. import app

from ..db import db_session
from ..db.models import Group, build_group_tree_db
from ..util.validation import validate_form_types
from ..util.tree import set_quota_sums, set_renames, set_params


@app.route('/edit', methods=['POST'])
def edit_groups_form():
    data = defaultdict(dict)
    for k, value in request.form.iteritems():
        group, parameter = k.split('+')
        data[group][parameter] = value

    errors = list()
    for grpname in data:
        data[grpname], e = validate_form_types(data[grpname])
        errors.extend(e)

    if errors:
        return render_template('edit_group.html', errors=errors)

    db_groups = Group.query.all()

    set_params(db_groups, data)

    root = build_group_tree_db(db_groups)

    try:
        set_quota_sums(db_groups, root)
        set_renames(db_groups, data)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('edit_groups_form'))
    else:
        # Objects in session.dirty are not necessarily modified if the set-attribute
        # is not different than the current one
        if any(x for x in db_session.dirty if db_session.is_modified(x)):
            flash("Everything OK, changes committed!")
        else:
            flash("No changes were made!", "nochange")

        db_session.commit()

    return redirect(url_for('main_menu'))
