import config as c
import MySQLdb
import sys

import logging

log = logging.getLogger()


def get(curclass=None):
    try:
        con = MySQLdb.connect(**c.db)
        cur = con.cursor(cursorclass=curclass)
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        sys.exit(1)

    return con, cur


def run(query):
    con, cur = get()
    try:
        cur.execute(query)
        con.commit()
        cur.close()
        con.close()
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        sys.exit(1)
