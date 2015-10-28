import gq.config as config

DATABASE_URI = 'mysql://%(user)s:%(passwd)s@%(host)s/%(db)s' % config.db
APP_NAME = 'Teir 3'
DEBUG = False

ADMIN_USER = 'willsk'
SESSION_COOKIE_NAME = 'gqweb_s_{0}'.format(APP_NAME.replace(' ', '_'))

T3ENABLE = True

LOG_FILE = '/tmp/gq_{0}_log'.format(APP_NAME.replace(' ', '_'))

# XXX: NOT REALLY USED IN PROD: Do the following and put in environs
#
#   $ tr -c -d '[:alnum:][!#$%&*.,]' < /dev/urandom | head -c 20
#
SECRET_KEY = 'CHANGE_ME!! - kvzUuR&LQ77x$&&smTFG.[U8QA]0'
# SESSION_COOKIE_SECURE = True
