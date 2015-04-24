# Parameters shared by QBalance software

# Db Connection parameters
dbhost = 'database.rcf.bnl.gov'
database = 'group_quotas'
dbuser = 'atlas_groupmod'
dbpass = 'zF@KmmZt?F'
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


# **************** Configuration variables and information *****************
panda_server = "https://pandaserver.cern.ch:25443"
web_path = "/server/panda/getJobStatisticsWithLabel"

# Queues to watch, map of PANDA Name -> Condor Group name
queues = {
    'BNL_PROD_MCORE': 'group_atlas.prod.mp',
    'BNL_ATLAS_2': 'group_atlas.prod.test',
    'BNL_PROD': 'group_atlas.prod.production',
    'ANALY_BNL_SHORT': 'group_atlas.analysis.short',
    'ANALY_BNL_LONG': 'group_atlas.analysis.long',
}

# Hours to look back for last change
lookback = 1

# Query Skeletons
get_Mysql_groups = 'SELECT %s FROM %s;'
get_Mysql_priority_list = 'SELECT %s FROM %s;'
get_Mysql_queue_amounts = 'SELECT %s FROM %s WHERE %s >= DATE_SUB(NOW(), INTERVAL %d HOUR) AND %s="%s";'
get_Mysql_queue_avg = 'SELECT AVG(%s) FROM %s WHERE %s >= DATE_SUB(NOW(), INTERVAL %d HOUR) AND %s="%s";'
get_Mysql_Val = 'SELECT %s FROM %s WHERE %s="%s"'

set_Mysql_last_surplus_update = 'UPDATE %s SET %s=current_timestamp WHERE %s="%s";'
set_Mysql_surplus = 'UPDATE %s SET %s=%d WHERE %s="%s";'

analyze_logfile = "/home/mvjensen/atlasSurplus.log"
panda_logfile = "/home/mvjensen/queueLog.log"
