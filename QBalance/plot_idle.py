#!/usr/bin/python

import os
import config.dbconn as db
import numpy as np
import matplotlib.pyplot as plt

from subprocess import Popen, PIPE
from collections import defaultdict


con, cur = db.get()
cur.execute("""SELECT query_time, amount_in_queue FROM atlas_queue_log WHERE
    group_name="group_atlas.analysis.long" AND
    query_time >= DATE_SUB(NOW(), INTERVAL 10 DAY)
    ORDER BY query_time DESC
""")
data = cur.fetchall()
con.close()

time = [x[0] for x in data]
count = [x[1] for x in data]


plot_cmd = """\
#set terminal png transparent
set terminal png size 800, 600
set title "History between"
set ylabel "Count"
set xlabel "Mb"
set xrange [0:]
set grid
set boxwidth 60
set style fill transparent solid 0.27
plot "-" using 1:2 with boxes lc rgb"green" title "%(sum)d jobs total: made %(when)s"
"""


def generate_image():

    fp = os.tmpfile()
    fp.write(plot_cmd % f)
    fp.write("\n".join('%d %d' % (x, y) for x, y in sorted(data.items())))
    fp.seek(0)

    proc = Popen(["gnuplot"], stdin=fp, stderr=PIPE, stdout=PIPE)
    out, err = proc.communicate()
    fp.close()

    if proc.returncode != 0:
        print "GNuplot: %s" % err
        sys.exit(1)
    print out

