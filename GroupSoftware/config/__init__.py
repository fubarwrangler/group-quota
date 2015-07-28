# Parameters shared by QBalance software

# Db Connection parameters

db = {
    'host': 'localhost',
    'db': 'group_quotas',
    'passwd': 'CHANGEME',
    'user': 'gqu'
}

# Minutes to look back for last change
change_lookback = 30

# Minutes ago to average to consider for demand
demand_lookback = 160

# Percent decrease betwen halves in spike-calculation that would indicate
# a sufficiently fast decrease to not be considered for demand
pct_dec_spike = 60

analyze_logfile = "/home/mvjensen/atlasSurplus.log"
panda_logfile = '/scratch/panda_dump.log'
