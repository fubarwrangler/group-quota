# ===========================================================================
# Add file-handler logger to app for production / testing use
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================

from ..application import app

from logging import Formatter
from logging.handlers import RotatingFileHandler

ten_meg = 10 * 1024 ** 2


def log_setup(logfile, level):

    file_handler = RotatingFileHandler(logfile, maxBytes=ten_meg, backupCount=3)
    file_handler.setLevel(level)

    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(level)
