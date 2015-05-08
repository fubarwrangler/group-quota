#!/usr/bin/python

import MySQLdb
import logging

import config as c
from log import setup_logging

log = setup_logging(c.panda_logfile, backup=1, size_mb=20, level=logging.INFO)

from jobquery import module_names

modules = list()
for mod in module_names:
    modules.append(__import__(mod, fromlist=module_names))


def insert_to_db(data):
    try:
        con = MySQLdb.connect(host=c.dbhost, user=c.dbuser, passwd=c.dbpass,
                              db=c.database)

        cur = con.cursor()
        cur.executemany('INSERT INTO atlas_queue_log '
                        '(`group_name`, `amount_in_queue`) VALUES (%s, %s)',
                        statements)
        con.commit()
        cur.close()
        con.close()
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        return None


if __name__ == '__main__':
    statements = list()

    # For each module, generate a list of tuples of group_name,#idle by
    # calling the get_jobs() method of each module in jobquery/*.py
    for module in modules:
        statements.extend(module.get_jobs().items())

    insert_to_db(statements)
