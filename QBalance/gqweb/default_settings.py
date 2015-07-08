DATABASE_URI = 'mysql:///group_quotas'
TABLE_NAME = 'atlas_group_quotas'
DEBUG = True

# XXX: NOT REALLY USED IN PROD: Do the following and put in environs
#
#   $ tr -c -d '[:alnum:][!#$%&*.,]' < /dev/urandom | head -c 20
#
SECRET_KEY = 'ChAnGeMe!!'
