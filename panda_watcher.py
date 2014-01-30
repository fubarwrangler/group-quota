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

# When number of mcore jobs < threshold, consider it insufficient demand
threshold = 20

# Database parameters
dbtable = 'localt3_group_quotas'
dbhost = 'database.rcf.bnl.gov'
database = 'linux_farm'
dbuser = 'condor_update'
dbpass = 'XPASSX'

q_skel = 'UPDATE %s SET accept_surplus=%d WHERE group_name="%s"'


# **************************************************************************

def get_num_activated(qname):
    global webdata
    return webdata[qname]['managed']['activated']


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

for panda, queue, group in ((x, mcore_q[x], webdata.get(x)) for x in mcore_q):
    if not group:
        print "Warning: queue %s does not have any data for it!" % panda
        continue

    get_num_activated(panda)

    set_acceptsurplus(group, True)



