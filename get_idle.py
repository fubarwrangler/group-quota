#!/usr/bin/python

import MySQLdb
import logging
import sys

import gq.config.dbconn
import gq.config as c

from gq.log import setup_logging

log = setup_logging(c.panda_logfile, backup=3, size_mb=20, level=logging.INFO)

from gq.jobquery import module_names

modules = list()
for mod in module_names:
    modules.append(__import__(mod, fromlist=module_names))

# Days to keep old data around
keep_days = 30


def insert_to_db(data):
    try:
        con, cur = gq.config.dbconn.get()
        cur.executemany('INSERT INTO queue_log (`id`, `amount_in_queue`) '
                        'SELECT id, %s FROM groups WHERE group_name=%s',
                        statements)
        cur.execute('DELETE FROM queue_log WHERE '
                    'query_time < DATE_SUB(NOW(), INTERVAL %d DAY)' % keep_days)
        con.commit()
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        return None


if __name__ == '__main__':
    statements = list()

    # For each module, generate a list of tuples of group_name,#idle by
    # calling the get_jobs() method of each module in jobquery/*.py
    for module in modules:
        data = module.get_jobs()
        if data is None:
            sys.exit(1)
        statements.extend([tuple(reversed(x)) for x in data.items()])
    # print statements
    insert_to_db(statements)
