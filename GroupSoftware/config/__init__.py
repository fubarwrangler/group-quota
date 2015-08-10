# Parameters shared by QBalance software
import os

# Db Connection parameters
db = {
    'host': 'localhost',
    'db': 'atlas_groups',
    'passwd': os.environ.get('GQ_DBPASS', 'default'),
    'user': 'gqu'
}

# Minutes to look back for last change
change_lookback = 30

# Minutes ago to average to consider for demand
demand_lookback = 160

# Percent decrease betwen halves in spike-calculation that would indicate
# a sufficiently fast decrease to not be considered for demand
pct_dec_spike = 60

analyze_logfile = '/tmp/surplus_analysis.log'
panda_logfile = '/tmp/panda_dump.log'
