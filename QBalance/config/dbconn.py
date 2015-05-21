import config as c
import MySQLdb
import sys

import logging

log = logging.getLogger()


def get():
    try:
        con = MySQLdb.connect(**c.db)
        cur = con.cursor()
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
