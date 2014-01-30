#!/usr/bin/python

# *****************************************************************************
# Script to query PANDA for how many jobs are activated in each queue that
# could run multicore jobs and to toggle the accept_surplus flag for the
# single-core production queue.
#
# By: William Strecker-Kellogg -- willsk@bnl.gov -- 1/30/14
#
# *****************************************************************************

import sys
import MySQLdb
import urllib2
import logging
import cPickle as pickle

# **************** Configuration variables and information *****************
server = "pandaserver.cern.ch:25443"
path = "/server/panda/getJobStatisticsWithLabel"

main_queue = ('BNL_PROD', 'group_atlas.prod.production')

# Multicore queues to watch, map of PANDA Name -> Condor Group name
mcore_q = {
    'BNL_PROD_MCORE': 'group_atlas.prod.mp8',
    'BNL_ATLAS_2': 'group_atlas.prod.test',
    #'ANALY_BNL_SHORT': 'group_atlas.analysis.short',
}

logfile = "/tmp/panda_watcher.log"

# When number of mcore jobs < threshold, consider it insufficient demand
threshold = 20

# Database parameters
dbtable = 'localt3_group_quotas'
dbhost = 'database.rcf.bnl.gov'
database = 'linux_farm'
dbuser = 'condor_update'
dbpass = 'XPASSX'

q_skel = 'UPDATE %s SET accept_surplus=%d WHERE group_name="%s"'

logging.basicConfig(format="%(asctime)-15s (%(levelname)s) %(message)s",
                    filename=logfile, level=logging.DEBUG)
log = getLogger()

# **************************************************************************

def get_num_activated(data):
    return data['managed']['activated']


def set_acceptsurplus(queue, state):

    try:
        con = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpass,
                              db=database)
    except MySQLdb.Error as E:
        print "Error connecting to database: %s" % E
        sys.exit(1)

    cur = con.cursor()
    cur.execute(q_skel % (dbtable, queue))
    n = cur.rowcount
    cur.close()
    con.close()
    return n


webservice = urllib2.urlopen("https://%s/%s" % (server, path))
webdata = pickle.load(webservice)

n_multicore_activated = 0

for panda, queue, data in ((x, mcore_q[x], webdata.get(x)) for x in mcore_q):
    if not data:
        log.warning("queue %s not found on PANDA server!", panda)
        continue

    n = get_num_activated(data)
    log.debug("%s:%s has %d activated", panda, queue, n)
    n_multicore_activated += n


log.info("%d total activated multicore jobs", n_multicore_activated)

#set_acceptsurplus(group, True)


