# ===========================================================================
# Routes for displaying and editing the Tier-3 relationships
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import request, redirect, url_for, flash, Response, session, g

from ..application import app

from ..db import db_session
from ..db.models import T3Institute
from ..util.userload import admin_permission


@app.route('/t3institutes', methods=['POST'])
@admin_permission.require(403)
def add_remove_institutes():

    button_hit = request.form.get('bAct')

    if button_hit == 'rm':
        to_remove = set(request.form.getlist('rm_me'))
        for x in to_remove:
            T3Institute.query.filter_by(name=x).delete()
        if not to_remove:
            flash("Nothing selected to be removed", category='tmperror')
            return redirect(url_for('t3_institute'))

        db_session.flush()
        flash("Successfully removed %d institutes" % len(to_remove))

    elif button_hit == 'add':
        name = request.form.get('newname')
        short = request.form.get('newshort')
        grp = request.form.get('newgroup')
        db_session.add(T3Institute(name=name, shortname=short, group=grp))
        db_session.flush()

        app.logger.info("Added new institute: %s", name)

        flash("New group added: %s" % name)

    db_session.commit()
    return redirect(url_for('t3_institute'))


@app.route('/t3users', methods=['POST'])
@admin_permission.require(403)
def add_remove_t3user():

    button_hit = request.form.get('bAct')

    if button_hit == 'rm':
        to_remove = set(request.form.getlist('rm_me'))
        for x in to_remove:
            T3Institute.query.filter_by(name=x).delete()
        if not to_remove:
            flash("Nothing selected to be removed", category='tmperror')
            return redirect(url_for('t3_institute'))

        db_session.flush()
        flash("Successfully removed %d institutes" % len(to_remove))

    elif button_hit == 'add':
        name = request.form.get('newname')
        short = request.form.get('newshort')
        grp = request.form.get('newgroup')
        db_session.add(T3Institute(name=name, shortname=short, group=grp))
        db_session.flush()

        app.logger.info("Added new institute: %s", name)

        flash("New group added: %s" % name)

    db_session.commit()
    return redirect(url_for('t3_user'))
