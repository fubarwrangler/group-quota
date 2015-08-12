# ===========================================================================
# Things to do before view functions on a request like load identity and
# set up default users on first request.
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================

from flask import request, session, g
from flask.ext.principal import Identity, AnonymousIdentity, RoleNeed

from ..application import app, principals
from ..db import db_session
from ..db.models import User, Role
from ..util.userload import load_user_debug, load_user_header


@app.before_first_request
def default_users_and_roles():

    def add_unique(obj, attr='name'):
        c = type(obj)
        if not c.query.filter(getattr(c, attr) == getattr(obj, attr)).first():
            db_session.add(obj)

    admin_u = User(name=app.config['ADMIN_USER'], active=True,
                   comment="Default admin user")
    admin_role = Role(name='admin',   comment='Full administrator with all privileges')

    add_unique(admin_u)
    add_unique(admin_role)

    db_admin_role = Role.query.filter_by(name='admin').first()

    add_unique(Role(name='alter',   comment='Can add / remove groups'))
    add_unique(Role(name='edit',    comment='Can edit all group parameters'))
    add_unique(Role(name='balance', comment='Can rebalance quotas with EZ-Editor'))

    admin_u.roles.append(admin_role if not db_admin_role else db_admin_role)

    db_session.commit()


@principals.identity_loader
def load_identity():
    if request.path.startswith("/static/"):
        return AnonymousIdentity()

    reconfig = session.get('reload_roles', False)
    if reconfig:
        session.pop('reload_roles')
    username = session.get('user')
    if not username or reconfig:
        app.logger.info("New user loaded")

        if app.config['DEBUG']:
            username = load_user_debug(app.config['ADMIN_USER'])
        else:
            username = load_user_header('REMOTE_USER')
        session['user'] = username

    roles = session.get('roles')
    if not roles or reconfig:
        user = User.query.filter_by(name=username).first()
        if not user:
            g.user = 'anonymous'
            return AnonymousIdentity()
        roles = [role.name for role in user.roles] if user.active else []
        app.logger.info("New roles loaded: %s", roles)
        session['roles'] = roles
        session['active'] = user.active

    identity = Identity(username)
    if session.get('active'):
        for role in roles:
            identity.provides.add(RoleNeed(role))

    g.user = username
    g.roles = roles

    return identity
