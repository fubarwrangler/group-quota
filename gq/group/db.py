# Module to build group-tree from database

import sys
import logging
import datetime
import MySQLdb
import MySQLdb.cursors

from ..config import dbconn as db
from .. import config as c

from group import DemandGroup, QuotaGroup

log = logging.getLogger()


class TreeException(Exception):
    pass


def _get_groups(fields):
    """ Return groups from DB ordered by name appropriate for tree creation """

    query = 'SELECT %s FROM groups ORDER BY group_name' % ", ".join(fields)

    try:
        con, cur = db.get(curclass=MySQLdb.cursors.DictCursor)
        cur.execute(query)
        data = cur.fetchall()
        cur.close()
        con.close()
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        sys.exit(1)

    return data


def build_demand_groups_db(grpCLS=DemandGroup):
    fields = ('group_name', 'accept_surplus', 'surplus_threshold', 'weight',)
    return _build_groups_db(grpCLS, fields)


def build_quota_groups_db(grpCLS=QuotaGroup):
    fields = ('group_name', 'accept_surplus', 'quota', 'priority',)
    return _build_groups_db(grpCLS, fields)


def _build_groups_db(grp_CLS, fields, group_builder=_get_groups, root='<root>'):
    """ Build group tree from database, instantiating the class passed in
        @grp_CLS and querying the db-fields in @fields
    """

    root_group = grp_CLS(root)

    for data in group_builder(fields):

        parts = data['group_name'].split('.')
        my_name = parts[-1]

        # Find appropriate parent from string of full group-name
        parent = root_group
        for x in parts[:-1]:
            try:
                parent = parent[x]
            except KeyError:
                log.error("%s without parent found in DB", data['group_name'])
                raise TreeException("%s without parent found in DB" % data['group_name'])

        data['name'] = my_name
        data.pop('group_name')
        parent.add_child(grp_CLS(**data))

    return root_group


def update_surplus_flags(root):
    """ Compare the tree passed in @root to the database's accept_surplus flags
        and make changes to the DB if it differs, constrained by the
        last_surplus_update timestamp
    """

    con, cur = db.get()
    cur.execute("SELECT group_name, accept_surplus, last_surplus_update FROM groups")
    db_surplus = dict((x, (bool(y), z)) for x, y, z in cur.fetchall())
    year = (60 * 60) * 24 * 365
    now = datetime.datetime.now()

    # Since python <= 2.6 doesn't have a .total_seconds() method on timedeltas...
    # See: https://docs.python.org/2/library/datetime.html#datetime.timedelta.total_seconds
    seconds = lambda td: ((td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

    for group in root:
        db_accept, ts = db_surplus[group.full_name]
        if group.accept == db_accept:
            continue

        # last change ago in seconds or a year ago if not defined
        last_change = seconds(now - ts) if ts else year

        if last_change > c.change_lookback * 60:
            log.info("Changing %s from %s->%s", group.full_name,
                     not group.accept, group.accept)
            cur.execute("UPDATE groups SET last_surplus_update=now(), "
                        "accept_surplus=%s WHERE group_name=%s",
                        (group.accept, group.full_name))
        else:
            log.info("Would change %s from %s->%s, but was changed %d minutes ago",
                     group.full_name, not group.accept, group.accept, last_change / 60)

    con.commit()
    cur.close()
    con.close()
