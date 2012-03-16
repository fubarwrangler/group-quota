#!/usr/bin/python


import os
import ConfigParser

__all__ = ["AUTHORIZED_USERS", "FARM_USERS", "logfile", "TABLE", "db_config"]

cp = ConfigParser.ConfigParser()
cp.read(os.environ['CFGFILE'])

AUTHORIZED_USERS = [x.strip() for x in cp.get('user_access', 'update_access').split(",")]
FARM_USERS = [x.strip() for x in cp.get('user_access', 'full_access').split(",")]

logfile = cp.get('main', 'logfile')

db_config = {}
for k, v in cp.items("db"):
    db_config[k] = v

TABLE = db_config["table"]

del cp
