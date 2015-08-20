import gq.config as config

DATABASE_URI = 'mysql://%(user)s:%(passwd)s@%(host)s/%(db)s' % config.db
APP_NAME = 'ATLAS'
DEBUG = False

ADMIN_USER = 'willsk'
# APPLICATION_ROOT = '/farmapp/'
SESSION_COOKIE_NAME = 'gqweb_s_{0}'.format(APP_NAME)

LOG_FILE = '/tmp/gq_{0}_log'.format(APP_NAME)

# XXX: NOT REALLY USED IN PROD: Do the following and put in environs
#
#   $ tr -c -d '[:alnum:][!#$%&*.,]' < /dev/urandom | head -c 20
#
SECRET_KEY = 'ChAnGEmE!!-- aghhh'
# SESSION_COOKIE_SECURE = True
