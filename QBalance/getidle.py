#!/usr/bin/python

import MySQLdb
import logging

import config.dbconn

from log import setup_logging

log = setup_logging(c.panda_logfile, backup=1, size_mb=20, level=logging.INFO)

from jobquery import module_names

modules = list()
for mod in module_names:
    modules.append(__import__(mod, fromlist=module_names))

# Days to keep old data around
keep_days = 14


def insert_to_db(data):
    try:
        con, cur = config.dbconn.get()
        cur.executemany('INSERT INTO atlas_queue_log '
                        '(`group_name`, `amount_in_queue`) VALUES (%s, %s)',
                        statements)
        cur.execute('DELETE FROM atlas_queue_log WHERE '
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
        statements.extend(module.get_jobs().items())

    insert_to_db(statements)
