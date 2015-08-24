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

import gq.config as c
import gq.config.dbconn as db

from gq.group import AbstractGroup
from gq.group.db import _build_groups_db
from gq.log import setup_logging


log = setup_logging(None)


class BusyGroup(AbstractGroup):

    def __init__(self, name):
        super(BusyGroup, self).__init__(name)
        self.busy = 0


def get_condor_groups():
    """ Yield a series of tuples of (group, count) where count is the number
        of cpus (SlotWeight) of that group
    """

    def get_group_from_classad(g):
        return ".".join(g.split("@")[0].split(".")[:-1])

    # get info from condor
    proc = subprocess.Popen(["condor_status",  "-pool",  c.condor_cm,
                             "-constraint",  "AccountingGroup =!= UNDEFINED",
                             "-format",  "%s ",  "AccountingGroup", "-format",
                             "%s\\n", "Cpus"], stdout=subprocess.PIPE)
    for line in (x.strip('\n') for x in proc.stdout):
        if not line:
            continue
        ad, count = line.split()
        yield get_group_from_classad(ad), count
    proc.wait()


def populate_group_busy(groups):

    # Map group-name -> group-obj for faster searching by name
    active = dict([(x.full_name, x) for x in groups])

    for group, count in get_condor_groups():
        if group in active:
            active[group].busy += int(count)
        else:
            log.warning("Unknown group: %s", group)

    # Set intermediate nodes as sum of children
    for group in groups:
        if not group.is_leaf:
            group.busy = sum(x.busy for x in group.get_children())


def fill_busy_db(groups):
    con, cur = db.get()
    for g in groups:
        cur.execute('UPDATE groups SET busy = %d WHERE group_name = "%s"' %
                    (g.busy, g.full_name))
    cur.execute('UPDATE groups SET last_update = %s', datetime.datetime.now())
    con.commit()
    con.close()


if __name__ == '__main__':
    # Build group tree from groups that count the "busy" field in the db
    groups = _build_groups_db(BusyGroup, ('group_name',))

    # Fill tree with info from condor
    populate_group_busy(groups)

    # Update DB with info in group tree
    try:
        fill_busy_db(groups)
    except MySQLdb.Error as e:
        log.error("DB Error %d: %s", e.args[0], e.args[1])
        sys.exit(1)
