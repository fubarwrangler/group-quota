from flask import request
from flask.ext.principal import RoleNeed, Permission


def load_user_header(header='REMOTE_USER'):
    user = request.headers.get(header)
    return user


def load_user_debug(user):
    return user


_admin_role = RoleNeed('admin')

admin_permission = Permission(_admin_role)
edit_permission = Permission(RoleNeed('edit'), _admin_role)
balance_permission = Permission(RoleNeed('balance'), _admin_role)
add_remove_permission = Permission(RoleNeed('alter'), _admin_role)
