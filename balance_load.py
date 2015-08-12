#!/usr/bin/python

import optparse
import logging
import sys

import gq.group.db as group_db
import gq.group.idlejobs as idle
import gq.group.balance as balance
import gq.config as c

from gq.log import setup_logging


def log_group_tree(groups):
    # Log group tree
    for group in reversed(list(groups)):
        log.info(group.color_str())

parser = optparse.OptionParser(
    epilog="Script to balance the accept-surplus flag for ATLAS"
)

parser.add_option("-d", "--debug", action="store_true",
                  help="Enable debug mode for logging")
parser.add_option("-l", "--logfile", action="store", default=c.analyze_logfile,
                  help="File to log information to ('-' for stderr)")
options, args = parser.parse_args()

loglevel = logging.DEBUG if options.debug else logging.INFO

log = setup_logging(options.logfile, backup=3, size_mb=40, level=loglevel)

field_map = {'group_name': 'name',
             'accept_surplus': 'surplus',
             'surplus_threshold': 'threshold',
             'weight': 'weight'}

if __name__ == "__main__":
    try:
        groups = group_db.build_demand_groups_db()
        idle.populate_demand(groups)

        log.info("Current Groups:")
        log_group_tree(groups)
        balance.calculate_surplus(groups)
        log.info("Groups after calculation:")
        log_group_tree(groups)
        group_db.update_surplus_flags(groups)
    except Exception as E:
        log.exception("Uncaught exception!")
        sys.exit(1)
