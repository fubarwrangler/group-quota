import gq.config as config
import logging

DATABASE_URI = 'mysql://%(user)s:%(passwd)s@%(host)s/%(db)s' % config.db
DEBUG = True
DB_ECHO = 0
APP_NAME = 'ATLAS'

DBPOOL_RECYCLE = 3600 * 3

ADMIN_USER = 'willsk'

T3ENABLE = False

# Used only if not in DEBUG mode
LOG_FILE = '/tmp/group_quota_{0}.log'.format(APP_NAME)
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

# XXX: NOT REALLY USED IN PROD: Do the following and put in environs
#
#   $ tr -c -d '[:alnum:][!#$%&*.,]' < /dev/urandom | head -c 20
#
# is 20 enough? 20 * log_2(26*2 + 10 + 8) ~ 122 bits of entropy
#
SECRET_KEY = 'ChAnGEmE!!-- rZB[6ogb#e#lzz.rXmr&'
# SESSION_COOKIE_SECURE = True
