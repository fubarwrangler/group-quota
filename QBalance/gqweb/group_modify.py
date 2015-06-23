# =============================================================================
# Methods for adding / removing groups and keeping the tree intact!
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# =============================================================================
from flask import render_template, redirect, url_for, flash, request
from . import app

from database import db_session
from models import Group, build_group_tree_db, set_quota_sums


def remove_groups(candidates, tree):
    bad_removes = list()
    warned = set()
    for group in (tree.find(x) for x in candidates):
        stranded = set(x.full_name for x in group) - candidates
        if stranded - warned:
            bad_removes.append((group.full_name, stranded - warned))
        warned |= stranded
    return bad_removes

group_defaults = {
    'group_name': None,
    'quota': None,
    'priority': 10.0,
    'weight': 0.0,
    'surplus_threshold': 0,
}


def new_group_fits(data, tree):

    newname = data['group_name']
    if tree.find(newname):
        return "Group %s already exists" % newname

    if newname.count('.') >= 1:
        parent = ".".join(newname.split('.')[:-1])
        if not tree.find(parent):
            return "New group <strong>%s</strong> must have" \
                   " a parent in the tree (<u>%s</u>)" % \
                   (newname, parent)

    missing_fields = set(group_defaults) - set(data)
    if missing_fields:
        misslist = ", ".join(sorted(missing_fields))
        return "New group needs the following fields defined: %s" % misslist

import quota_edit

@app.route('/addrm', methods=['POST'])
def add_groups_post():

    button_hit = request.form.get('bAct')

    db_groups = Group.query.all()
    root = build_group_tree_db(db_groups)

    if button_hit == 'rm':
        to_remove = set(request.form.getlist('rm_me'))
        if not to_remove:
            return render_template('group_add_rm.html', gen_err="Nothing selected to be removed")

        bad_removes = remove_groups(to_remove, root)

        if bad_removes:
            return render_template('group_add_rm.html', rmerrors=bad_removes)
        elif to_remove:
            for obj in db_groups:
                if obj.group_name in to_remove:
                    db_session.delete(obj)
            flash("Successfully removed %d group(s)" % len(to_remove))

    elif button_hit == 'add':
        newgrp = dict([(k.split('+')[1], v) for k, v in request.form.iteritems()
                       if v and k.startswith('new+')])
        if 'group_name' in newgrp:
            group, errors = quota_edit.validate_form_types(newgrp)
            if errors:
                return render_template('group_add_rm.html', typeerrors=errors)
            errors = new_group_fits(group, root)
            if errors:
                return render_template('group_add_rm.html', gen_err=errors)

            new_in_db = Group(**group)
            db_session.add(new_in_db)

            flash("New group added: %s" % newgrp)
        else:
            return render_template('group_add_rm.html',
                                   gen_err="Nothing to add, no group-name defined!")


set_quota_sums(db_groups, build_group_tree_db(Group.query.all()))
    db_session.commit()
    return redirect(url_for('main_menu'))
