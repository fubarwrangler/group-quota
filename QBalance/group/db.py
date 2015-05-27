#!/usr/bin/python
# Module to build group-tree from database

import sys
import logging
import datetime

from group import Group
import MySQLdb

import config.dbconn as db
import config as c

log = logging.getLogger()

__all__ = ['build_groups_db', 'update_surplus_flags']


def build_groups_db():
    """ Build group tree from database """

    root_group = Group('<root>')

    for name, weight, surplus, threshold in _get_groups():
        parts = name.split('.')
        myname = parts[-1]

        # Find appropriate parent from string of full group-name
        parent = root_group
        for x in parts[:-1]:
            parent = parent[x]

        parent.add_child(Group(myname, weight, surplus, threshold))

    return root_group


def _get_groups():
    """ Return groups from DB ordered by name appropriate for tree creation """

    fields = ('group_name', 'weight', 'accept_surplus', 'surplus_threshold')

    query = 'SELECT %s FROM atlas_group_quotas ORDER BY group_name' % ", ".join(fields)

    try:
        con, cur = db.get()
        cur.execute(query)
        data = cur.fetchall()
        cur.close()
        con.close()
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        sys.exit(1)

    return data


def update_surplus_flags(root):
    """ Compare the tree passed in @root to the database's accept_surplus flags
        and make changes to the DB if it differs, constrained by the
        last_surplus_update timestamp
    """

    con, cur = db.get()
    cur.execute("SELECT group_name, accept_surplus, last_surplus_update FROM atlas_group_quotas")
    db_surplus = dict((x, (bool(y), z)) for x, y, z in cur.fetchall())
    year = (60 * 60) * 24 * 365
    now = datetime.datetime.now()

    for group in root:
        db_accept, ts = db_surplus[group.full_name]
        if group.accept == db_accept:
            continue

        # last change ago in seconds or a year ago if not defined
        last_change = (now - ts).total_seconds() if ts else year

        if last_change > c.lookback * 60:
            log.info("Changing %s from %s->%s", group.full_name,
                     not group.accept, group.accept)
            cur.execute("UPDATE atlas_group_quotas SET last_surplus_update=now(), "
                        "accept_surplus=%s WHERE group_name=%s",
                        (group.accept, group.full_name))
        else:
            log.info("Would change %s from %s->%s, but was changed %d minutes ago",
                     group.full_name, not group.accept, group.accept, last_change / 60)

    con.commit()
    cur.close()
    con.close()
