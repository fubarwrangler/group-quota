# =============================================================================
# Methods for adding / removing groups and keeping the tree intact!
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# =============================================================================
from flask import render_template, redirect, url_for, flash
from . import app

from database import db_session
from models import Group, build_group_tree_db, type_map, build_group_tree_formdata


@app.route('/addrm', methods=['POST'])
def add_groups_post():

    root = build_group_tree_db(Group.query.all())

    # root
    return redirect(url_for('main_menu'))
