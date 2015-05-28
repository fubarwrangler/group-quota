# Module to build group-tree from database

import sys
import logging
import datetime
import MySQLdb
import MySQLdb.cursors

import config.dbconn as db
import config as c

log = logging.getLogger()

__all__ = ['build_groups_db', 'update_surplus_flags']


def build_groups_db(grp_CLS, field_map):
    """ Build group tree from database, mapping from db-field names to
        group-class parameter names via @field_map and instantiating
        the class passed in @grp_CLS
    """

    root_group = grp_CLS('<root>')

    for data in _get_groups(field_map):
        args = dict([(field_map.get(key, key), data[key]) for key in data])

        parts = data['group_name'].split('.')
        my_name = parts[-1]

        # Find appropriate parent from string of full group-name
        parent = root_group
        for x in parts[:-1]:
            try:
                parent = parent[x]
            except KeyError:
                log.error("%s without parent found in DB", data['group_name'])
                sys.exit(1)

        args['name'] = my_name
        parent.add_child(grp_CLS(**args))

    return root_group


def _get_groups(fields):
    """ Return groups from DB ordered by name appropriate for tree creation """

    query = 'SELECT %s FROM atlas_group_quotas ORDER BY group_name' % ", ".join(fields)

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
