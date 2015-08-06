from flask import request


def load_user_header(header='REMOTE_USER'):
    user = request.headers.get(header)
    return user


def load_user_debug(user):
    return user
