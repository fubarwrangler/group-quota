import gq.config as config
import logging

DATABASE_URI = 'mysql://%(user)s:%(passwd)s@%(host)s/%(db)s' % config.db
TABLE_NAME = 'groups'
DEBUG = True
APP_NAME = 'ATLAS'

DBPOOL_RECYCLE = 3600 * 3

ADMIN_USER = 'willsk'

T3ENABLE = False

# Used only if not in DEBUG mode
LOG_FILE = '/tmp/group_quota_{0}.log'.format(APP_NAME)
LOG_LEVEL = logging.INFO

# XXX: NOT REALLY USED IN PROD: Do the following and put in environs
#
#   $ tr -c -d '[:alnum:][!#$%&*.,]' < /dev/urandom | head -c 20
#
SECRET_KEY = 'ChAnGEmE!!-- rZB[6ogb#e#lzz.rXmr&'
# SESSION_COOKIE_SECURE = True
