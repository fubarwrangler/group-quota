#!/usr/bin/python

import sys

from group import Group
import MySQLdb

import config as c
from log import setup_logging

log = setup_logging(None)

__all__ = ['build_groups']


def build_groups(root_group):

    for name, weight, surplus, threshold in get_groups():
        parts = name.split('.')
        myname = parts[-1]

        # Find appropriate parent from string of full group-name
        parent = root_group
        for x in parts[:-1]:
            parent = parent[x]

        parent.add_child(Group(myname, weight, surplus, threshold))


def get_groups():
    """ Return groups from DB ordered by name appropriate for tree creation """

    fields = ('group_name', 'weight', 'accept_surplus', 'surplus_threshold')

    query = 'SELECT %s FROM atlas_group_quotas ORDER BY group_name' % ", ".join(fields)

    try:
        con = MySQLdb.connect(host=c.dbhost, user=c.dbuser, db=c.database, passwd=c.dbpass)
        cur = con.cursor()
        cur.execute(query)
        data = cur.fetchall()
        cur.close()
        con.close()
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        sys.exit(1)

    return data

root = Group('<root>')
build_groups(root)
root.print_tree()
