# ===========================================================================
# Methods to receive changes from ez-editor form in page
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================

from collections import defaultdict
from . import app

from flask import request, render_template, redirect, url_for, flash
from database import db_session
from models import (Group, build_group_tree_db, validate_form_types,
                    build_group_tree_formdata, set_quota_sums)


@app.route('/ezq/<parent>', methods=['POST'])
def ezedit_chooser():

    return redirect(url_for('main_menu'))
