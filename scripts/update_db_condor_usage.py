#!/usr/bin/python

# Desc: Simple script to read the condor usage information from the atlas central
#       manager and record it in the atlas_group_quota database on database (cronjob)
#
# By: William Strecker-Kellogg -- willsk@bnl.gov
#
# CHANGELOG:
#   08/24/15: rewrite for using gq library

import sys
import MySQLdb
import datetime
import subprocess

from collections import defaultdict

import gq.config as c
import gq.config.dbconn as db

from gq.log import setup_logging


log = setup_logging(None)
con, cur = db.get()


def get_groups():
    cur.execute("SELECT group_name FROM groups")
    g = set(x[0] for x in cur)
    cur.close()
    if not g:
        log.error('No groups defined')
        sys.exit(1)
    return g


def get_condor_data(groups):
    # get info from condor
    proc = subprocess.Popen(["condor_status",  "-pool",  c.condor_cm,
                             "-constraint",  "AccountingGroup =!= UNDEFINED",
                             "-format",  "%s ",  "AccountingGroup", "-format",
                             "%s\\n", "Cpus"], stdout=subprocess.PIPE)

    active = defaultdict(int)

    for group, count in ((y.split()) for y in proc.communicate()[0].split("\n") if y):
        group = ".".join(group.split("@")[0].split(".")[:-1])
        if group in groups:
            active[group] += int(count)
        else:
            log.warning("Unknown group: %s", group)

    for group in (x for x in groups if x not in active):
        active[group] = 0

    return active

if __name__ == '__main__':
    usage = get_condor_data(get_groups())
    try:
        cur = con.cursor()
        for x in usage:
            cur.execute('UPDATE groups SET busy = %d WHERE group_name = "%s"' %
                        (usage[x], x))
        cur.execute('UPDATE groups SET last_update = %s', datetime.datetime.now())
        cur.close()
    except MySQLdb.Error as e:
        log.error("DB Error %d: %s", e.args[0], e.args[1])
        con.rollback()
        con.close()
    else:
        con.commit()
        con.close()
