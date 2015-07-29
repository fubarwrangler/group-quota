# =============================================================================
# Methods for adding / removing groups and keeping the tree intact!
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# =============================================================================
from flask import render_template, redirect, url_for, flash, request

from .. import app

from ..db import db_session
from ..db.models import Group, build_group_tree_db
from ..util.validation import validate_form_types
from ..util.tree import set_quota_sums, new_group_fits, remove_groups


@app.route('/addrm', methods=['POST'])
def add_groups_post():

    button_hit = request.form.get('bAct')

    db_groups = Group.query.all()
    root = build_group_tree_db(db_groups)

    if button_hit == 'rm':
        to_remove = set(request.form.getlist('rm_me'))
        if not to_remove:
            flash("Nothing selected to be removed", category='tmperror')
            return redirect(url_for('add_groups'))

        bad_removes = remove_groups(to_remove, root)

        if bad_removes:
            return render_template('group_add_rm.html', rmerrors=bad_removes)

        for obj in db_groups:
            if obj.group_name in to_remove:
                db_session.delete(obj)
        db_session.flush()
        flash("Successfully removed %d group(s)" % len(to_remove))

    elif button_hit == 'add':
        newgrp = dict([(k.split('+')[1], v) for k, v in request.form.iteritems()
                       if v and k.startswith('new+')])
        if 'group_name' not in newgrp:
            flash("Nothing to add, no group-name defined", category='tmperror')
            return redirect(url_for('add_groups'))

        group, errors = validate_form_types(newgrp)
        if errors:
            return render_template('group_add_rm.html', errors=errors)
        error = new_group_fits(group, root)
        if error:
            return render_template('group_add_rm.html', error=error)

        new_in_db = Group(**group)
        db_session.add(new_in_db)
        db_session.flush()

        flash("New group added: %s" % newgrp['group_name'])

    # Rebalance db and tree from inserted/deleted but-not-committed objects
    new_db = Group.query.all()
    set_quota_sums(new_db, build_group_tree_db(new_db))

    db_session.commit()
    return redirect(url_for('add_groups'))
