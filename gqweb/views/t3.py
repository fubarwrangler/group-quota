# ===========================================================================
# Routes for displaying and editing the Tier-3 relationships
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from flask import request, redirect, url_for, flash, render_template

from ..application import app

from ..db import db_session
from ..db.models import Group, build_group_tree_db
from ..db.t3models import T3Institute, T3User
from ..util.userload import t3_admin_permission

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import subqueryload


@app.route('/t3')
def t3view():
    userquery = T3User.query.options(subqueryload(T3User.institute)).order_by(T3User.name)
    return render_template('t3/list.html', users=userquery.all())


@app.route('/t3/users')
def t3_user():
    inst = request.args.get('institute')
    if inst:
        userquery = T3User.query.filter_by(affiliation=inst)
        filterinstquery = T3Institute.query.filter(T3Institute.name == inst)
        if len(filterinstquery.all()) == 0:
            return render_template('errors/noresults.html')
    else:
        userquery = T3User.query

    instquery = T3Institute.query

    users = sorted(userquery.all(), key=lambda x: (x.name, x.affiliation))
    return render_template('t3/users.html', users=users, institutes=instquery.all(),
                           filtered=filterinstquery.first() if inst else None)


@app.route('/t3/institutes')
def t3_institute():
    root = build_group_tree_db(Group.query.all())
    inst = T3Institute.query.options(subqueryload(T3Institute.users))
    institutes = sorted(inst.all(), key=lambda x: x.name)
    existing = set([x.group for x in institutes])
    available = sorted([x for x in root if x.is_leaf and x.full_name not in existing],
                       key=lambda x: x.full_name)
    return render_template('t3/institutes.html', inst=institutes, avail=available)


@app.route('/t3/api/user', methods=['POST'])
@t3_admin_permission.require(403)
def edit_user():
    data = request.form
    username = data['origname']
    affiliation = data['origaffil']

    user = T3User.query.filter_by(name=username, affiliation=affiliation).first()
    user.fullname = data['fullname']
    user.affiliation = data['affiliation']
    user.name = data['name']

    try:
        db_session.commit()
    except IntegrityError:
        flash("Duplicate key created, cannot have the same username at the "
              "same institution!", category='error')
    else:
        app.logger.info("Edit T3 User: %s", username)
        flash("Edit T3 User: %s" % username)

    return redirect(url_for('t3_user'))


@app.route('/t3/api/institute', methods=['POST'])
@t3_admin_permission.require(403)
def edit_institute():
    data = request.form
    orig = data['origname']
    name = data['name']

    if orig != name and T3Institute.query.filter_by(name=name).first():
        flash('Cannot change name of %s, %s already exists' %
              (orig, name), category='error')
    else:
        institute = T3Institute.query.filter_by(name=orig).first()
        institute.name = name
        institute.fullname = data['fullname']
        institute.group = data['group']
        try:
            db_session.commit()
        except IntegrityError:
            flash("Duplicate key: institutions must be unique ", category='error')
        else:
            app.logger.info("Edit T3 Institute: %s", orig)
            flash("Edited T3 Institute: %s" % orig)

    return redirect(url_for('t3_institute'))


@app.route('/t3/institutes', methods=['POST'])
@t3_admin_permission.require(403)
def add_remove_institutes():

    button_hit = request.form.get('bAct')

    if button_hit == 'rm':
        to_remove = set(request.form.getlist('rm_me'))
        if not to_remove:
            flash("Nothing selected to be removed", category='tmperror')
            return redirect(url_for('t3_institute'))

        for x in to_remove:
            T3Institute.query.filter_by(name=x).delete()

        db_session.commit()
        flash("Successfully removed %d institutes" % len(to_remove))

    elif button_hit == 'add':
        name = request.form.get('newname')
        short = request.form.get('newshort')
        grp = request.form.get('newgroup')
        if not name or not short:
            flash('Must include names for the institute', category='tmperror')
            return redirect(url_for('t3_institute'))
        try:
            db_session.add(T3Institute(name=short, fullname=name, group=grp))
            db_session.flush()
        except IntegrityError as e:
            flash(e.message, category='error')
        else:
            app.logger.info("Added new institute: %s", name)
            flash("New group added: %s" % name)
            db_session.commit()

    return redirect(url_for('t3_institute'))


@app.route('/t3/users', methods=['POST'])
@t3_admin_permission.require(403)
def add_remove_t3user():

    button_hit = request.form.get('bAct')

    if button_hit == 'rm':
        to_remove = request.form.getlist('rm_me')
        if not to_remove:
            flash("Nothing selected to be removed", category='tmperror')
            return redirect(url_for('t3_user'))

        for item in to_remove:
            n, a = item.split(' ')
            T3User.query.filter_by(name=n, affiliation=a).delete()

        db_session.commit()
        flash("Successfully removed %d users" % len(to_remove))

    elif button_hit == 'add':
        name = request.form.get('newname')
        full = request.form.get('newgiven')
        grp = request.form.get('newgroup')
        if not name or not full or not grp:
            flash('All fields required for new user', category='tmperror')
            return redirect(url_for('t3_user'))
        try:
            db_session.add(T3User(name=name, fullname=full, affiliation=grp))
            db_session.flush()
        except IntegrityError as e:
            flash(e.message, category='error')
        else:
            app.logger.info("Added new institute: %s", name)
            flash("New group added: %s" % name)
            db_session.commit()

    return redirect(url_for('t3_user'))
