#!/usr/bin/python

import sys

from group import Group
import MySQLdb

import config as c
from log import setup_logging

log = setup_logging(None)


def build_groups(root_group):
    pg = root_group
    for name, weight, surplus, threshold in get_groups():
        myname = name.split('.')[-1]
        parent_name = '.'.join(name.split('.')[:-1])
        print "Names", myname, parent_name, pg.full_name
        ng = Group(myname, weight, surplus, threshold)

        if pg is root_group or name.startswith(pg.full_name):
            print "Add child to root or child group"
            pg.add_child(ng)
            pg = ng
        else:
            print "Backtrack to find", parent_name
            pg = root_group.find(parent_name)
            pg.add_child(ng)
            pg = ng
        print "\n"


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
