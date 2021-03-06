# Module to set up logging for this software

import logging
from logging.handlers import RotatingFileHandler


def setup_logging(filename, backup=2, size_mb=150, level=logging.DEBUG):

    fmt_str = "%(asctime)-15s (%(levelname)-7s) %(message)s"

    if filename is None or filename == '-':
        logging.basicConfig(format=fmt_str, level=level)
        return logging.getLogger()

    log = logging.getLogger()
    handler = RotatingFileHandler(filename, maxBytes=size_mb * 1024**2,
                                  backupCount=backup)
    handler.setFormatter(logging.Formatter(fmt_str))
    log.addHandler(handler)
    log.setLevel(level)

    return log
