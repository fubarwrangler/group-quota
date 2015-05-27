# Parameters shared by QBalance software

# Db Connection parameters

db = {
    'host': 'localhost',
    'db': 'group_quotas',
    'port': 3333,
    'passwd': 'CHANGEME',
    'user': 'gqu'
}

dbtable = 'atlas_group_quotas'
queue_log_table = 'atlas_queue_log'

# DB Fields
accept_surplus = 'accept_surplus'
amount_in_queue = 'amount_in_queue'
busy = 'busy'
group_name = 'group_name'
last_surplus_update = 'last_surplus_update'
last_update = 'last_update'
query_time = 'query_time'
quota = 'quota'
threshold = 'surplus_threshold'
weight = 'weight'


# Minutes to look back for last change
lookback = 60

analyze_logfile = "/home/mvjensen/atlasSurplus.log"
panda_logfile = "/home/mvjensen/queueLog.log"
