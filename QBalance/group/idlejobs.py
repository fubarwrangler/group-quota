#!/usr/bin/python

# Module to give a count of the idle jobs with a simple moving average of
# the last hour.

import logging
import config.dbconn as db

log = logging.getLogger()


def get_db_demand(con, name, window=120):
    """ Return list of demand-values in last hour unless there are too few then
        return None and warn about it
    """

    fewest_datapoints = 5

    where = 'query_time >= DATE_SUB(NOW(), INTERVAL %d MINUTE) AND group_name="%s"' % \
            (window, name)

    query = "SELECT amount_in_queue FROM atlas_queue_log WHERE %s" % where
    cur = con.cursor()
    count = cur.execute(query)
    data = cur.fetchall()
    cur.close()

    if count < fewest_datapoints:
        log.warning('%d datapoints for %s (< %d), not considering for demand',
                    count, name, fewest_datapoints)
        return None

    return [x[0] for x in data]


# FIXME: Is this needed!?
def get_avg_demand(con, name, window=60):
    where = 'query_time >= DATE_SUB(NOW(), INTERVAL %d MINUTE) AND group_name="%s"' % \
            (window, name)
    avg_query = "SELECT AVG(amount_in_queue) FROM atlas_queue_log WHERE %s" % where
    cur = con.cursor(avg_query)
    cur.execute(avg_query)
    avg = cur.fetchall()
    cur.close()

    return avg


# TODO: Add real implementation
def spike_detected(data):
    return False


def get_average(data):
    """ Midpoint sampling to help smooth possibly irregularly-sampled data """

    assert(len(data) > 1)
    avg = 0
    for n in range(len(data) - 1):
        avg += data[n] + (data[n + 1] - data[n]) / 2.0
    return avg / float(len(data) - 1)


def populate_demand(root):

    con = db.get()[0]
    for node in root.leaf_nodes():
        name = node.full_name
        last_hour = get_db_demand(con, node.full_name)
        if last_hour is None:
            log.info("Queue %s has insufficient data for demand calc", name)
            demand = 0
        elif spike_detected(last_hour):
            log.info("Queue %s -- spike detected", name)
            demand = 0
        else:
            demand = int(round(get_average(last_hour)))

        log.info('real-demand for %s set -> %d', name, demand)
        node.demand = demand

    con.close()
