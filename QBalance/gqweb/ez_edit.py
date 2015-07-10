# ===========================================================================
# Methods to validate edited quota info from form data and make changes
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================

from itertools import groupby
from . import app

from flask import request, render_template, redirect, url_for, flash
from database import db_session
from models import (Group, build_group_tree_db, validate_form_types,
                    build_group_tree_formdata, set_quota_sums)
from math import floor


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


    seen = set()

    # quota of parent of any member of "highest" level (no indexing on set)
    for level, groups in enumerate(levels):
        # level = len(levels) - idx
        total_q = root.find(levels[level][0]).parent.quota
        app.logger.info("lvl %d: Groups %s -> Total q = %s", level, groups, total_q)

        # XXX: FIXME: NEED TO FIX GROUPING HERE
        # largest_remainder([new_quotas[x] for x in groups])


    # for group in (x for x in root if x.full_name in new_quotas):
    #     app.logger.info("Set group %s quota %f -> %f", group.full_name, group.quota, new_quotas[group.full_name])
    #     group.quota = new_quotas[group.full_name]
    #     group.qchange = True
    #
    # seen = set()
    # for group in filter(lambda x: hasattr(x, 'qchange') and x not in seen, root):
    #     app.logger.debug('%s?????', group)
    #     siblings = [x for x in group.siblings() if x not in seen]
    #     app.logger.info("sib (%f): %s", group.parent.quota, siblings)
    #     seen |= set(siblings)


    flash(new_quotas, category="stay")

    return redirect(url_for('main_menu'))


# Rounding according to this algorithm: http://stackoverflow.com/questions/13483430/
def largest_remainder(data):
    ifloor = lambda x: int(floor(x))

    new_data = map(ifloor, data)
    total = sum(data)
    partial = sum(new_data)

    extra = total - partial

    app.logger.debug("%s : %s : %f : %f", data, new_data, total, partial)

    for idx, n in enumerate(sorted(data, key=lambda x: x - floor(x))):
        extra -= 1
        app.logger.debug("Give +1 to %f", new_data[idx])
        new_data[idx] += 1
        if extra <= 0.0:
            break

    app.logger.info('%s == %s', sum(new_data), total)

    return new_data
