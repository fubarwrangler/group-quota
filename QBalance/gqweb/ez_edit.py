# ===========================================================================
# Methods to validate the quotas from the ez-slider and make changes
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================

from . import app

from flask import request, redirect, url_for, flash
from database import db_session
from models import Group, build_group_tree_db
from math import floor


# Rounding according to this algorithm: http://stackoverflow.com/questions/13483430/
def largest_remainder(data, total):
    ifloor = lambda x: int(floor(x))

    new_data = map(ifloor, data)
    # total = sum(data)
    partial = sum(new_data)

    # How many extra integers to give out
    extra = total - partial

    app.logger.debug("lr: %s : %s : %f : %f", data, new_data, total, partial)

    # In largest decimal order
    decimal_order = map(ifloor, sorted(data, key=lambda x: floor(x) - x))

    n = 0
    while extra > 0.0:
        new_data[new_data.index(decimal_order[n])] += 1
        extra -= 1
        n += 1

    app.logger.debug('%s == %s: %s', sum(new_data), total, new_data)

    return new_data


def validate_quotas(root):
    for group in (x for x in root if not x.is_leaf):
        if group.quota != sum(x.quota for x in group.get_children()):
            flash("Invalid quotas from EZ-Edit (bug?), found at: %s" % group,
                  category="error")
            return False
    return True


@app.route('/ezq/<groupparent>', methods=['POST'])
def ezedit_chooser(groupparent):

    new_quotas = dict(
        map(lambda x: (x[0], float(x[1])),                # 3. and convert value to float.
            filter(lambda x: not x[0].endswith('+take'),  # 2. filter non-quota inputs,
                   request.form.iteritems())              # 1. For each form key-value pair,
            )
        )
    app.logger.info(new_quotas)

    db_groups = Group.query.all()
    root = build_group_tree_db(db_groups)

    for x in root.breadth_first():
        if x.full_name in new_quotas:
            new_root = x.parent
            break

    # Root group doesn't have quota by default!
    if new_root is root:
        root.quota = sum(x.quota for x in root.get_children())

    seen = set()
    for parent in new_root.breadth_first():
        if parent.is_leaf:
            continue
        children = [x for x in parent.get_children() if x not in seen]
        seen |= set(children)
        adj_q = largest_remainder([new_quotas[x.full_name] for x in children], parent.quota)
        for g, q in zip(children, adj_q):
            g.quota = q
            dbobj = next(x for x in db_groups if x.group_name == g.full_name)
            dbobj.quota = q
            app.logger.info("!! SET %s q=%d", g, g.quota)

    if validate_quotas(root):
        flash("Update quotas under: %s" % new_root)
        db_session.commit()
    else:
        db_session.rollback()

    return redirect(url_for('ezedit_chooser', groupparent=groupparent))
