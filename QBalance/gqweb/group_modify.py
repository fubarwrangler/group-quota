# =============================================================================
# Methods for adding / removing groups and keeping the tree intact!
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# =============================================================================
from flask import render_template, redirect, url_for, flash, request
from . import app

from database import db_session
from models import Group, build_group_tree_db, type_map, build_group_tree_formdata


def remove_groups(candidates, tree):
    bad_removes = list()
    warned = set()
    flash("TO remove: %s" % candidates)
    for group in (tree.find(x) for x in candidates):
        stranded = set(x.full_name for x in group) - candidates
        if stranded - warned:
            bad_removes.append("Cannot remove intermediate group %s" % group.full_name +
                               " unless all its children are selected too because"
                               "it strands %s" % ", ".join(stranded - warned))
        warned |= stranded
    return bad_removes


def check_new_grp(formdata, tree):

    newname = formdata['']
    parent = ".".join(newname.split('.')[:-1])
    if not tree.find(parent):
        return "New group must have a parent who exists in the tree"

@app.route('/addrm', methods=['POST'])
def add_groups_post():

    db_groups = Group.query.all()
    root = build_group_tree_db(db_groups)

    to_remove = set(request.form.getlist('rm_me'))
    bad_removes = remove_groups(to_remove, root)
    # flash("Got %s" % request.form.items())

    for x in request.form.iteritems():
        pass

    # errors = (('a', 'b', 'c'),)
    errors = None

    if False:
        db_session.commit()

    return render_template('group_add_rm.html', typeerrors=errors, rmerrors=bad_removes, groups=root)

    #return redirect(url_for('main_menu'))
