#!/usr/bin/python

# Module to give a count of the idle jobs with a simple moving average of
# the last hour.

import logging
import config.dbconn as db
import config as c

log = logging.getLogger()


def get_db_demand(con, name, window=c.demand_lookback):
    """ Return list of demand-values in last hour unless there are too few then
        return None and warn about it
    """

    fewest_datapoints = 8

    where = 'query_time >= DATE_SUB(NOW(), INTERVAL %d MINUTE) AND group_name="%s"' % \
            (window, name)

    query = "SELECT amount_in_queue FROM queue_log NATURAL JOIN " + \
            "groups WHERE %s" % where
    cur = con.cursor()
    count = cur.execute(query)
    data = cur.fetchall()
    cur.close()

    if count < fewest_datapoints:
        log.warning('%d datapoints for %s (< %d), not considering for demand',
                    count, name, fewest_datapoints)
        return None

    return [x[0] for x in data]


# XXX: This is poorly named
def spike_detected(data):
    """ Look for rapid-decrease between halves of dataset or if second-half is
        a flat zero. If so return True so there is no demand considered.
    """

    # Half the data and look at the averages separately
    first, second = data[:len(data)/2], data[len(data)/2:]
    m, n = get_average(first), get_average(second)

    # If the entire second half is zero, consider it exhausted and return True
    if m > 0 and n == 0:
        log.debug("Second half zero, spike to true")
        return True

    # Avoid div-by-zero and too-small-to-matter for percentage change
    if m < 5:
        log.debug("First half too small, no change-detect possible")
        return False

    d = 100 * (n - m) / m
    log.debug("First avg: %d, second avg: %d, change: %.2f%%", m, n, d)

    if d < -c.pct_dec_spike:
        log.debug("Decrease sufficient between halves, spike to true")
        return True

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
        average = int(round(get_average(last_hour))) if last_hour is not None else 0

        if last_hour is None:
            log.warning("Queue %s has insufficient data for demand calc", name)
            demand = 0
        elif average > 0 and spike_detected(last_hour):
            log.info("Queue %s -- spike detected", name)
            demand = 0
        else:
            demand = average

        log.debug('real-demand for %s set -> %d', name, demand)
        node.demand = demand

    con.close()
