# ===========================================================================
# Methods to validate edited quota info from form data and make changes
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================

from itertools import groupby
from . import app

from flask import request, redirect, url_for, flash
# from database import db_session
from models import Group, build_group_tree_db
from math import floor, ceil


@app.route('/ezq/<parent>', methods=['POST'])
def ezedit_chooser(parent):

    new_quotas = dict(
        map(lambda x: (x[0], float(x[1])),                # 3. and convert value to float.
            filter(lambda x: not x[0].endswith('+take'),  # 2. filter non-quota inputs,
                   request.form.iteritems())              # 1. For each form key-value pair,
            )
        )
    app.logger.info(new_quotas)

    db_groups = Group.query.all()
    root = build_group_tree_db(db_groups)
    dotcount = lambda x: x.count('.')

    levels = list()
    for level, data in groupby(sorted(new_quotas, key=dotcount), dotcount):
        levels.append([x for x in data])

    child_of = lambda c, p: c.startswith(p)

    # quota of parent of any member of "highest" level (no indexing on set)
    for level, groups in enumerate(levels):
        # level = len(levels) - idx
        total_q = root.find(groups[0]).parent.quota
        app.logger.info("lvl %d: Groups %s -> Total q = %s", level, groups, total_q)

        # XXX: FIXME: NEED TO FIX GROUPING HERE
        grpgrp = list()
        if level > 0:
            for parent in levels[level - 1]:
                grpgrp.append([x for x in groups if child_of(x, parent)])
        else:
            grpgrp.append(groups)
        grpgrp = filter(bool, grpgrp)

        app.logger.info("Child groupings: %s", grpgrp)
        for childgroups in grpgrp:
            adj_quotas = largest_remainder([new_quotas[x] for x in childgroups])
            for i, x in enumerate(childgroups):
                root.find(childgroups[i]).quota = adj_quotas[i]

    flash(new_quotas, category="stay")

    return redirect(url_for('main_menu'))


# Rounding according to this algorithm: http://stackoverflow.com/questions/13483430/
def largest_remainder(data, total):
    ifloor = lambda x: int(floor(x))

    new_data = map(ifloor, data)
    # total = sum(data)
    partial = sum(new_data)

    # How many extra integers to give out
    extra = total - partial

    app.logger.debug("%s : %s : %f : %f", data, new_data, total, partial)

    # In largest decimal order
    decimal_order = map(ifloor, sorted(data, key=lambda x: floor(x) - x))
    app.logger.debug('dorder: %s', decimal_order)

    n = 0
    while extra > 0.0:
        new_data[new_data.index(decimal_order[n])] += 1
        extra -= 1
        n += 1

    app.logger.info('%s == %s: %s', sum(new_data), total, new_data)

    return new_data
