# ===========================================================================
# Define functions here to load the user -- in our case we load it from
# the apache basic-auth header, but a user/password scheme could be supported
# here using flask-login or something. Also defines Roles & Permissions.
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================

from flask import request, session
from flask_principal import RoleNeed, Permission


def load_user_header(header='REMOTE_USER'):
    user = request.environ.get(header)
    return user


def load_user_debug(user):
    return user


def can_change_group(gname):
    # Empty list is no restrictions
    group_acl = session.get('groups', [])
    if not group_acl:
        return True

    return any(gname.startswith(x) for x in group_acl)


_admin_role = RoleNeed('admin')

admin_permission = Permission(_admin_role)
edit_permission = Permission(RoleNeed('edit'), _admin_role)
balance_permission = Permission(RoleNeed('balance'), _admin_role)
add_remove_permission = Permission(RoleNeed('alter'), _admin_role)
t3_admin_permission = Permission(RoleNeed('t3admin'), _admin_role)
