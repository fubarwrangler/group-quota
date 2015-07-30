DATABASE_URI = 'sqlite:////home/willsk/this.db'
TABLE_NAME = 'atlas_group_quotas'
DEBUG = True

ADMIN_ROLE = 'admin'
DEFAULT_USER = 'willsk'
DEFAULT_USER_ROLE = 'admin'  # XXX: CHANGE FOR PROD


# XXX: NOT REALLY USED IN PROD: Do the following and put in environs
#
#   $ tr -c -d '[:alnum:][!#$%&*.,]' < /dev/urandom | head -c 20
#
SECRET_KEY = 'ChAnGEmE!!-- rZB[6ogb#e#lzz.rXmr&'
