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


@app.route('/ezq/<parent>', methods=['POST'])
def ezedit_chooser(parent):

    new_quotas = dict(
        map(lambda x: (x[0], float(x[1])),                # 3. and convert value to float.
            filter(lambda x: not x[0].endswith('+take'),  # 2. filter non-quota inputs,
                   request.form.iteritems())              # 1. For each form key-value pair,
            )
        )
    app.logger.info(new_quotas)

    # db_groups = Group.query.all()
    # root = build_group_tree_db(db_groups)

    dotcount = lambda x: x.count('.')
    levels = list()

    # Rounding according to this algorithm: http://stackoverflow.com/questions/13483430/
    for level, data in groupby(sorted(new_quotas, key=dotcount), dotcount):
        levels.append([x for x in data])

    for idx, group in enumerate(levels):
        pass

    flash(new_quotas, category="stay")

    return redirect(url_for('main_menu'))
