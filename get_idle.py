#!/usr/bin/python

import optparse
import logging
import glob
import sys
import imp

import os.path as path

import gq.config as c

from gq.group.idlejobs import insert_data
from gq.log import setup_logging


def load_module_path(arg):
    mods = None
    name = lambda x: path.basename(x).split('.')[0]

    if not path.exists(arg):
        log.error("Module path '%s' does not exist", arg)
        return None
    elif path.isdir(arg):
        pyfiles = glob.glob(path.join(arg, '*.py'))
        pyfiles = filter(lambda x: '__init__.py' not in x, pyfiles)
        mods = [imp.load_source(name(x), x) for x in pyfiles]
    elif path.isfile(arg):
        mods = [imp.load_source(name(arg), arg)]

    return mods


parser = optparse.OptionParser(
    usage="%prog [-h] [-d] [-l <log>] MODULE_SOURCE",
    description="Script to populate group-quota db with jobs\n\n",
    epilog="""MODULE_SOURCE: A module or directory containing modules that
contain code to gather information about numbers of idle jobs. Each module
must have a get_jobs() function defined that returns a dictionary mapping
group_name -> #idle"""
)

parser.add_option("-d", "--debug", action="store_true",
                  help="Enable debug mode for logging")
parser.add_option("-l", "--logfile", action="store", default=c.panda_logfile,
                  help="File to log information to ('-' for stderr)")
options, args = parser.parse_args()

loglevel = logging.DEBUG if options.debug else c.log_level

log = setup_logging(options.logfile, backup=3, size_mb=20, level=loglevel)

if not args:
    from gq.jobquery import module_names
    modules = list()
    for mod in module_names:
        modules.append(__import__(mod, fromlist=module_names))
elif len(args) != 1:
    print >>sys.stderr, "Wrong number of arguments!"
    modules = None
else:
    modules = load_module_path(args[0])

if modules is None:
    sys.exit(1)
elif len(modules) < 1:
    log.warning("No modules found to be loaded!")
    sys.exit(0)

log.debug("Loaded %d module(s): %s", len(modules), ", ".join(x.__name__ for x in modules))

# Days to keep old data around
keep_days = 30

if __name__ == '__main__':
    sys.exit(0 if insert_data(modules, keep_days) else 1)
