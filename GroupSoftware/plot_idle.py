#!/usr/bin/python

import sys

import config.dbconn as db
import matplotlib.pyplot as plt

QUEUE = sys.argv[1]

con, cur = db.get()
cur.execute("SELECT surplus_threshold FROM atlas_group_quotas WHERE group_name='%s'" % QUEUE)
threshold = cur.fetchall()[0][0]
cur.execute("""SELECT query_time, amount_in_queue FROM atlas_queue_log WHERE
    id=(SELECT id FROM atlas_group_quotas WHERE group_name="%s") AND
    query_time >= DATE_SUB(NOW(), INTERVAL 5 DAY)
    ORDER BY query_time DESC
""" % QUEUE)
data = cur.fetchall()
con.close()

time = [x[0] for x in data]
count = [x[1] for x in data]


plt.plot(time, count)
plt.axhline(threshold, color='red', linestyle='-.')
plt.show()
