#!/usr/bin/python

# *****************************************************************************
# Script to query PANDA for how many jobs are activated in
# each queue and to update the queue_log accordingly.
#
#   1. Query PANDA for data queues
#   2. Identify active queues
#   3. Insert the queue size into the log for each queue
#
# By: Mark Jensen -- mvjensen@rcf.rhic.bnl.gov -- 6/11/14
#
# *****************************************************************************

import sys
import MySQLdb
import urllib2
import cPickle
import logging

from log import setup_logging
import config as c

log = setup_logging(c.panda_logfile, backup=1, size_mb=20, level=logging.INFO)

# **************************************************************************

# According to J. Hover, this is the definitive test for if a queue is analysis
is_analysis = lambda q: q.startswith("ANALY")


def get_num_activated(queue, data):
    # Production queues are under 'managed', analysis under 'user', just the
    # way it is in PANDA, go figure!?

    key = 'user' if is_analysis(queue) else 'managed'
    if 'activated' in data.get(key, {}):
        return data[key]['activated']
    else:
        return 0


def set_current_queue(con, queue, amount):
    cur = con.cursor()
    cur.execute('INSERT INTO '+c.queue_log_table+' VALUES (%s, %s, NOW())', (queue, amount))
    log.debug("%s added to %s", queue, c.queue_log_table)
    n = cur.rowcount
    con.commit()
    cur.close()
    return n


def do_main():
    log.info("Accessing panda at %s", c.panda_server)
    try:
        webservice = urllib2.urlopen(c.panda_server + c.web_path, timeout=30)
        # This is so horribly insecure, I can't believe it!
        webdata = cPickle.load(webservice)

    except urllib2.URLError:
        log.error("Timeout accessing PANDA webservice, exit...")
        return 1

    try:
        con = MySQLdb.connect(host=c.dbhost, user=c.dbuser, passwd=c.dbpass,
                              db=c.database)
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        return None

    for panda_q, data in ((x, webdata.get(x)) for x in c.queues):
        if not data:
            log.warning("queue %s not found but not used either", panda_q)
            set_current_queue(con, c.queues[panda_q], 0)
            continue
        else:
            log.debug("queue %s: %s", panda_q, data)

        n = get_num_activated(panda_q, data)
        log.info("%s:%s has %d activated", panda_q, c.queues[panda_q], n)
        set_current_queue(con, c.queues[panda_q], n)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(do_main())
    except Exception:
        log.exception("Uncaught exception")
        sys.exit(1)
