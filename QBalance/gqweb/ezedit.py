# ===========================================================================
# Methods to receive changes from ez-editor form in page
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================

from . import app
from flask import request, redirect, url_for, flash


@app.route('/ezq/<parent>', methods=['POST'])
def ezedit_chooser(parent):

    flash(request.form)

    return redirect(url_for('main_menu'))
