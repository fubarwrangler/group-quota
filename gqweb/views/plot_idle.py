# =============================================================================
# Plot the idle jobs from the past time window per queue with matplotlib
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# =============================================================================
from flask import render_template, make_response, url_for, flash, request, redirect

from ..application import app

from ..db.models import q_log as log_t, Group
from sqlalchemy import select

from datetime import timedelta, datetime

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

group_t = Group.__table__


@app.route('/plot/<group>')
def plot(group):

    app.logger.info("Plot %s", group)
    q = select([log_t.c.query_time, log_t.c.amount_in_queue], log_t.c.id == group_t.c.id)
    q = q.where(group_t.c.group_name == group)
    q = q.where(log_t.c.query_time >= datetime.now() - timedelta(hours=2))
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
