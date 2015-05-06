# Module to set up logging for this software

import logging
from logging.handlers import RotatingFileHandler
import sys


def setup_logging(filename, backup=2, size_mb=150, level=logging.DEBUG):

    fmt_str = "%(asctime)-15s (%(levelname)s) %(message)s"

    if '-d' in sys.argv:
        logging.basicConfig(format=fmt_str, level=logging.DEBUG)
        return logging.getLogger()

    log = logging.getLogger()
    handler = RotatingFileHandler(filename, maxBytes=size_mb * 1024**2,
                                  backupCount=backup)
    handler.setFormatter(logging.Formatter(fmt_str))
    log.addHandler(handler)
    log.setLevel(level)

    return log
