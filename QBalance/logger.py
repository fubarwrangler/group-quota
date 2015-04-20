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
import logging
import cPickle

# **************** Configuration variables and information *****************
panda_server = "https://pandaserver.cern.ch:25443"
web_path = "/server/panda/getJobStatisticsWithLabel"

# Queues to watch, map of PANDA Name -> Condor Group name
queues = {
    'BNL_PROD_MCORE': 'group_atlas.prod.mp',
    'BNL_ATLAS_2': 'group_atlas.prod.test',
    'BNL_PROD': 'group_atlas.prod.production',
    'ANALY_BNL_SHORT': 'group_atlas.analysis.short',
    'ANALY_BNL_LONG': 'group_atlas.analysis.long',
}

# Database parameters
dbtable = 'queue_log'
dbhost = 'old-db.rcf.bnl.gov'
database = 'atlas_demand'
dbuser = 'group_edit'
dbpass = 'atlas'

q_current = 'INSERT INTO %s VALUES ("%s", %d, NOW())'

logfile = "/home/mvjensen/dynamicgroups/Logger/queueLog.log"

logging.basicConfig(format="%(asctime)-15s (%(levelname)s) %(message)s",
                    filename=None if '-d' in sys.argv else logfile,
                    level=logging.DEBUG if '-d' in sys.argv else logging.INFO)

log = logging.getLogger()

print("\nSTART OF TEST")
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
    
def set_current_queue(queue, amount):
    try:
        con = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpass,
                              db=database)
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        return None
    cur = con.cursor()
    cur.execute(q_current % (dbtable, queue, amount))
    log.info("%s added to %s", queue, dbtable)
    print('\n')
    n = cur.rowcount
    con.commit()
    cur.close()
    con.close()
    return n


def do_main():
    log.info("Accessing panda at %s", panda_server)
    try:
        webservice = urllib2.urlopen(panda_server + web_path, timeout=30)
        # This is so horribly insecure, I can't believe it!
        webdata = cPickle.load(webservice)

    except urllib2.URLError:
        log.error("Timeout accessing PANDA webservice, exit...")
        return 1

    for panda_q, data in ((x, webdata.get(x)) for x in queues):
        if not data:
            log.warning("queue %s not found but not used either", panda_q)
            set_current_queue(queues[panda_q], 0)
            continue
        else:
            log.debug("queue %s: %s", panda_q, data)

        n = get_num_activated(panda_q, data)        
        log.info("%s:%s has %d activated", panda_q, queues[panda_q], n)
        set_current_queue(queues[panda_q], n)
       
    print("END OF TEST\n")
    return 0
    

if __name__ == '__main__':
    try:
        sys.exit(do_main())
    except Exception:
        log.exception("Uncaught exception")
        sys.exit(1)
