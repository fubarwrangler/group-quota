import config

DATABASE_URI = 'mysql://%(user)s:%(passwd)s@%(host)s/%(db)s' % config.db
TABLE_NAME = 'groups'
DEBUG = True

ADMIN_USER = 'willsk'
APPLICATION_ROOT = '/farmdebug/'
SESSION_COOKIE_NAME = 'gqweb_session'

# ADMIN_USER = 'Administrator'


# XXX: NOT REALLY USED IN PROD: Do the following and put in environs
#
#   $ tr -c -d '[:alnum:][!#$%&*.,]' < /dev/urandom | head -c 20
#
SECRET_KEY = 'ChAnGEmE!!-- rZB[6ogb#e#lzz.rXmr&'
# SESSION_COOKIE_SECURE = True
