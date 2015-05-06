#!/usr/bin/python

import sys

from group import Group
import MySQLdb

import config as c
from log import setup_logging

log = setup_logging(None)


def build_groups(root_group):

    for name, weight, surplus, threshold in get_groups():
        lst = name.split('.')
        myname = lst[-1]

        ng = Group(myname, weight, surplus, threshold)

        parent = root_group
        for x in lst[:-1]:
            parent = parent.get_child(x)
        parent.add_child(ng)


def get_groups():
    """ Return groups from DB ordered by count of .'s in them, appropriate
        for group-tree creation
    """

    fields = ('group_name', 'weight', 'accept_surplus', 'surplus_threshold')

    query = 'SELECT %s FROM atlas_group_quotas' % ", ".join(fields)

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

    return sorted(data, key=lambda x: x[0])


root = Group('<root>')
build_groups(root)
root.print_tree()
