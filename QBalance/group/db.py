#!/usr/bin/python
# Module to build group-tree from database

import sys
import logging

from group import Group
import MySQLdb

import config as c

log = logging.getLogger()

__all__ = ['build_groups_db']


def build_groups_db():

    root_group = Group('<root>')

    for name, weight, surplus, threshold in get_groups():
        parts = name.split('.')
        myname = parts[-1]

        # Find appropriate parent from string of full group-name
        parent = root_group
        for x in parts[:-1]:
            parent = parent[x]

        parent.add_child(Group(myname, weight, surplus, threshold))

    return root_group


def get_groups():
    """ Return groups from DB ordered by name appropriate for tree creation """

    fields = ('group_name', 'weight', 'accept_surplus', 'surplus_threshold')

    query = 'SELECT %s FROM atlas_group_quotas ORDER BY group_name' % ", ".join(fields)

    try:
        con, cur = c.database.get()
        cur.execute(query)
        data = cur.fetchall()
        cur.close()
        con.close()
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        sys.exit(1)

    return data
