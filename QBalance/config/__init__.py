# Parameters shared by QBalance software

# Db Connection parameters

db = {
    'host': 'localhost',
    'db': 'group_quotas',
    'port': 3306,
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
lookback = 21

# Query Skeletons
get_Mysql_groups = 'SELECT %s FROM %s;'
get_Mysql_priority_list = 'SELECT %s FROM %s;'
get_Mysql_queue_amounts = 'SELECT %s FROM %s WHERE %s >= DATE_SUB(NOW(), INTERVAL %d MINUTE) AND %s="%s";'
get_Mysql_queue_avg = 'SELECT AVG(amount_in_queue) FROM atlas_queue_log WHERE query_time >= DATE_SUB(NOW(), INTERVAL %d MINUTE) AND %s="%s"'
get_Mysql_Val = 'SELECT %s FROM %s WHERE %s="%s"'

set_Mysql_last_surplus_update = 'UPDATE %s SET %s=current_timestamp WHERE %s="%s";'
set_Mysql_surplus = 'UPDATE %s SET %s=%d WHERE %s="%s";'

analyze_logfile = "/home/mvjensen/atlasSurplus.log"
panda_logfile = "/home/mvjensen/queueLog.log"
