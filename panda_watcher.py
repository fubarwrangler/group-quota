#!/usr/bin/python

# *****************************************************************************
# Script to query PANDA for how many jobs are activated in each queue that
# could run multicore jobs and to toggle the accept_surplus flag for the
# single-core production queue accordingly.
#
# For now the logic is simple:
#   1. if there are any multicore jobs: prod-surplus -> false
#   2. if there are 1core-prod jobs and no multicore jobs: prod-surplus -> true
#
# By: William Strecker-Kellogg -- willsk@bnl.gov -- 1/30/14
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

single_core_prod = set(['BNL_PROD'])
mcore_queues = set(['BNL_ATLAS_2', 'BNL_PROD_MCORE'])

# Multicore queues to watch, map of PANDA Name -> Condor Group name
queues = {
    'BNL_PROD_MCORE': 'group_atlas.prod.mp',
    'BNL_ATLAS_2': 'group_atlas.prod.test',
    'BNL_PROD': 'group_atlas.prod.production',
    'ANALY_BNL_SHORT': 'group_atlas.analysis.short',
    'ANALY_BNL_LONG': 'group_atlas.analysis.long',
}

threshold = 4
logfile = "/tmp/panda_watcher.log"

# Database parameters
dbtable = 'atlas_group_quotas'
dbhost = 'database.rcf.bnl.gov'
database = 'linux_farm'
dbuser = 'condor_update'
dbpass = 'XPASSX'

q_skel = 'UPDATE %s SET accept_surplus=%d WHERE group_name="%s"'

logging.basicConfig(format="%(asctime)-15s (%(levelname)s) %(message)s",
                    filename=None if '-d' in sys.argv else logfile,
                    level=logging.DEBUG if '-d' in sys.argv else logging.INFO)
log = logging.getLogger()
# **************************************************************************

# According to J. Hover, this is the definitive test for if a queue is analysis
is_analysis = lambda q: q.startswith("ANALY")


def get_num_activated(qname, data):
    # Production queues are under 'managed', analysis under 'user', just the
    # way it is in PANDA, go figure!?

    key = 'user' if is_analysis(qname) else 'managed'
    if 'activated' in data.get(key, {}):
        return data[key]['activated']
    else:
        return 0


def set_acceptsurplus(queue, state):

    try:
        con = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpass,
                              db=database)
    except MySQLdb.Error as E:
        log.error("Error connecting to database: %s" % E)
        return None

    cur = con.cursor()
    cur.execute(q_skel % (dbtable, state, queue))
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

    activated = {}

    for panda_q, data in ((x, webdata.get(x)) for x in queues):
        if not data:
            if panda_q in mcore_queues | single_core_prod:
                log.error("Critical queue %s not found on PANDA server!", panda_q)
                return 1
            else:
                log.warning("queue %s not found but not used either", panda_q)
                continue
        else:
            log.debug("queue %s: %s", panda_q, data)

        n = get_num_activated(panda_q, data)

        activated[panda_q] = n

        log.debug("%s:%s has %d activated", panda_q, queues[panda_q], n)

    prod_activated = sum(activated[x] for x in queues if x in single_core_prod)
    log.info("%d total activated singlecore production jobs", prod_activated)

    no_mcore_demand = [x for x in mcore_queues if activated[x] <= threshold]
    if no_mcore_demand and prod_activated > threshold:
        log.info("Mcore queues '%s': no activated jobs", ",".join(no_mcore_demand))
        surplus = True
    else:
        surplus = False

    changed = False

    log.debug("Production queue accept_surplus should be %s", surplus)
    for group_name in (queues[x] for x in queues if x in single_core_prod):
        r = set_acceptsurplus(group_name, int(surplus))
        if r is None:
            return 1
        elif r > 0:
            changed = True
            log.info("%s accept_surplus changed -> %s", group_name, surplus)
        else:
            log.debug("%s: no change", group_name)

    if not changed:
        log.info("Surplus is %s, nothing was changed", surplus)

    return 0

if __name__ == '__main__':
    try:
        sys.exit(do_main())
    except Exception:
        log.exception("Uncaught exception")
        sys.exit(1)
