# =============================================================================
# Plot the idle jobs from the past time window per queue with matplotlib
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# =============================================================================
from flask import render_template, make_response, url_for, redirect

from ..application import app

from ..db.models import q_log as log_t, Group
from sqlalchemy import select, distinct

from datetime import timedelta, datetime

# Set environment so it works on webserver where $HOME/.matplotlib isn't writable
import os
os.environ['MPLCONFIGDIR'] = "/var/tmp/"

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

group_t = Group.__table__


@app.route('/plot')
def plot_page():
    q = select([distinct(group_t.c.group_name)], log_t.c.id == group_t.c.id)
    q = q.where(log_t.c.query_time >= datetime.now() - timedelta(hours=4))
    q = q.order_by(group_t.c.group_name)
    groups = list(x[0] for x in q.execute())

    return render_template('plot.html', groups=groups)


@app.route('/plot/<group>')
def plot_group(group):
    return render_template('plot.html', group=group)


@app.route('/plot/img/<group>')
def plot_image(group):

    q = select([log_t.c.query_time, log_t.c.amount_in_queue], log_t.c.id == group_t.c.id)
    q = q.where(group_t.c.group_name == group)
    q = q.where(log_t.c.query_time >= datetime.now() - timedelta(hours=4))
    q = q.order_by(log_t.c.query_time)

    thresh = Group.query.filter_by(group_name=group).first().surplus_threshold
    data = list(q.execute())
    if len(data) < 1:
        return redirect(url_for('main_menu'))

    png_data = StringIO()
    # Zip() with a '*' is a projection, who knew?
    time, count = zip(*data)

    fig = Figure()
    fig.set_size_inches(11, 8.5)
    axis = fig.add_subplot(1, 1, 1)
    axis.plot(time, count, marker='.')
    axis.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M'))
    fig.autofmt_xdate()

    axis.axhline(thresh, color='red', linestyle='-.')
    canvas = FigureCanvas(fig)
    canvas.print_png(png_data)
    response = make_response(png_data.getvalue())
    response.mimetype = 'image/png'
    return response
