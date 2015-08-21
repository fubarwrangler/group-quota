# ===========================================================================
# Methods to validate the quotas from the ez-slider and make changes
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import request, redirect, url_for, flash

from ..application import app

from ..db import db_session
from ..db.models import Group, build_group_tree_db
from ..util.rounding import largest_remainder
from ..util.userload import balance_permission


def validate_quotas(root):
    for group in (x for x in root if not x.is_leaf):
        if group.quota != sum(x.quota for x in group.get_children()):
            flash("Invalid quotas from EZ-Edit (bug?), found at: %s" % group,
                  category="error")
            return False
    return True


@app.route('/ezq/<groupparent>', methods=['POST'])
@balance_permission.require(403)
def ezedit_chooser(groupparent):

    new_quotas = dict(
        map(lambda x: (x[0], float(x[1])),                # 3. and convert value to float.
            filter(lambda x: not x[0].endswith('+take'),  # 2. filter non-quota inputs,
                   request.form.iteritems())              # 1. For each form key-value pair,
            )
        )

    db_groups = Group.query.all()
    root = build_group_tree_db(db_groups)

    for x in root.breadth_first():
        if x.full_name in new_quotas:
            new_root = x.parent
            break

    # Root group doesn't have quota by default!
    if new_root is root:
        root.quota = sum(x.quota for x in root.get_children())

    changed = False
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
            if dbobj.quota != q:
                app.logger.info("EZ-Change quota for %s: %d -> %d",
                                dbobj.group_name, dbobj.quota, q)
                dbobj.quota = q
                changed = True

    if changed and validate_quotas(root):
        flash("Updated quotas under: %s" % new_root)
        db_session.commit()
    else:
        flash("No changes made")
        db_session.rollback()

    return redirect(url_for('ez_quota_chooser'))
