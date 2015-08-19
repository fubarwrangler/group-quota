# Parameters shared by QBalance software
import os
import sys
import os.path
import logging
import ConfigParser

_sources = ('/etc/gq.cfg', os.environ.get('GQ_CONFIG', ''))

_cfg = ConfigParser.ConfigParser()
_moduledir = os.path.dirname(os.path.realpath(__file__))
_defaultconfig = os.path.join(_moduledir, 'defaults.cfg')
try:
    _cfg.readfp(open(_defaultconfig))
except EnvironmentError:
    logging.error("Cannot read default config: %s", _defaultconfig)
    sys.exit(1)

_cfg.read(_sources)

# Db Connection parameters
db = {
    'host':     _cfg.get('mysql-db', 'host'),
    'db':       _cfg.get('mysql-db', 'database'),
    'user':     _cfg.get('mysql-db', 'user'),
    'passwd':   _cfg.get('mysql-db', 'password'),
}

change_lookback = _cfg.getint('params', 'change_lookback')

demand_lookback = _cfg.getint('params', 'demand_lookback')
pct_dec_spike = _cfg.getfloat('params', 'pct_dec_spike')

analyze_logfile = _cfg.get('logging', 'analyze_logfile')
panda_logfile = _cfg.get('logging', 'panda_logfile')

log_level = getattr(logging, _cfg.get('logging', 'level').upper())
