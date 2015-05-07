#!/usr/bin/python
# *****************************************************************************
# Get jobs from PANDA for appropriate groups (non-grid)
# All modules must have the get_jobs() method
#
# *****************************************************************************

import urllib2
import pickle
import logging

log = logging.getLogger()

# **************************************************************************

# Queues to watch, map of PANDA Name -> Condor Group name
queues = {
    'BNL_PROD_MCORE':  'group_atlas.prod.mp',
    'BNL_ATLAS_2':     'group_atlas.prod.test',
    'BNL_PROD':        'group_atlas.prod.production',
    'ANALY_BNL_SHORT': 'group_atlas.analysis.short',
    'ANALY_BNL_LONG':  'group_atlas.analysis.long',
}

# **************** Configuration variables and information *****************
url = "https://pandaserver.cern.ch:25443/server/panda/getJobStatisticsWithLabel"

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


def get_jobs():
    log.info("Accessing panda at %s", url)
    try:
        webservice = urllib2.urlopen(url, timeout=30)
        # This is so horribly insecure, I can't believe it!
        webdata = pickle.load(webservice)

    except urllib2.URLError:
        log.error("Timeout accessing PANDA webservice, exit...")
        return None

    idle = {}

    for panda_q, data in ((x, webdata.get(x)) for x in queues):
        if not data:
            log.warning("queue %s not found but not used either", panda_q)
            idle[queues[panda_q]] = 0
            continue
        else:
            log.debug("queue %s: %s", panda_q, data)

        n = get_num_activated(panda_q, data)
        log.info("%s:%s has %d activated", panda_q, queues[panda_q], n)

        idle[queues[panda_q]] = n

    return idle
