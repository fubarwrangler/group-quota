#!/usr/bin/python

# Desc: This script checks, being very paranoid, for differences between the
#       database holding the atlas group quota information (on database) and the
#       current file held in 'QUOTA_FILE' below.  If there are any differences,
#       it backs up 'QUOTA_FILE' to 'QUOTA_BACKUP' and writes the changed quotas
#       to a temporary file before replacing the real 'QUOTA_FILE' with the
#       temporary one.  This is run as cronjob every 10 minutes
#
# By: William Strecker-Kellogg -- willsk@bnl.gov
#
# CHANGELOG:
#   8/10/10     v1.0 to be put into production
#   8/16/10     v1.5 email linux farm when changes are made
#   4/07/11     v2.0 email is configurable on the command line
#   6/15/11     v2.5 make reconfig optional, use logging and tempfile

# NOTE: This script works in conjuction with farmweb01:/var/www/cgi-bin/group_quota.py
#       and the farmweb01:/var/www/public/cronjobs/update_db_condor_usage.py, which
#       act as a database frontend and update the busy slots in each group respectively

import sys, os, os.path
import subprocess, time, smtplib
import logging, tempfile, shutil
import optparse, re
from email.MIMEText import MIMEText
import MySQLdb

QUOTA_FILE   = '/etc/condor/atlas-group-definitions'
QUOTA_BACKUP = '/etc/condor/atlas-group-definitions.previous'
LOGFILE      = '/etc/condor/group-def.log'
LOGLEVEL = logging.INFO

frmt = logging.Formatter("%(asctime)s %(name)s: (%(levelname)-6s)"
                         " %(message)s", "%m/%d %X")

log = logging.getLogger('quota_update')
log.setLevel(logging.DEBUG)


#file_handler = logging.FileHandler(LOGFILE)
file_handler = logging.StreamHandler()
file_handler.setLevel(LOGLEVEL)
file_handler.setFormatter(frmt)

log.addHandler(file_handler)

# Needed to run reconfig command below
os.environ['CONDOR_CONFIG'] = '/etc/condor/condor_config.atlas'


class Group(object):

    def __init__(self, name, quota=0, prio=10.0, surplus=False):
        if len(name) > 6 and name[:6] == "group_":
            self.name = name
        else:
            raise ValueError("Group names must start with 'group_'")

        self.quota = int(quota)
        self.prio = float(prio)
        self.surplus = str(bool(surplus)).upper()

    def __str__(self):
        msg  = '\n'
        msg += 'GROUP_QUOTA_%s = %d\n' % (self.name, self.quota)
        msg += 'GROUP_PRIO_FACTOR_%s = %.1f\n' % (self.name, self.prio)
        msg += 'GROUP_ACCEPT_SURPLUS_%s = %s\n' % (self.name, self.surplus)
        return msg

    def __cmp__(self, other):

        same = True
        for x in ("name", "quota", "prio", "surplus"):
            if getattr(self, x) != getattr(other, x):
                same = False
                break
        if same:
            return 0
        else:
            if self.name >= other.name:
                return 1
            else:
                return -1

class Groups(object):
    def __init__(self):
        self._groups = {}

    def add_group(self, name, quota, prio, surplus):
        if name in self._groups:
            raise ValueError("Cannot have groups with duplicated name: %s" % name)
        else:
            self._groups[name] = Group(name, quota, prio, surplus)

    def check_tree(self):

        bad = set()
        for grp in sorted(self._groups, key=lambda x: len(x.split(".")), reverse=True):
            parent = ".".join(grp.split(".")[:-1])
            if parent and parent not in self._groups:
                bad.add(grp)
        return bad

    def __str__(self):
        x = "GROUP_NAMES = %s\n" % ', '.join(sorted(self._groups))
        for grp in sorted(self._groups):
            x += str(self._groups[grp])
        return x

    def __iter__(self):
        return iter(sorted(self._groups.keys()))

    def __getitem__(self, name):
        return self._groups[name]

    def __len__(self):
        return len(self._groups)

    def __eq__(self, other):
        if len(self) == len(other):
            for x in self:
                pass


        return False



class DBGroups(Groups):
    def __init__(self, table, host="database.rcf.bnl.gov", user="db_query",
                              database="linux_farm"):

        super(DBGroups, self).__init__()

        try:
            con = MySQLdb.connect(db=database, host=host, user=user, connect_timeout=3)
            dbc = con.cursor()
            dbc.execute("SELECT group_name, quota, priority, accept_surplus "
                        "FROM %s ORDER BY group_name" % table)
        except MySQLdb.Error, e:
            log.error("DB Error %d: %s" % (e.args[0], e.args[1]))
            sys.exit(1)
        else:
            for x in dbc:
                self.add_group(*x)
            dbc.close()
            con.close()

        if self.check_tree():
            log.error("Invalid group configuration found")
            sys.exit(1)


class FileGroups(Groups):
    def __init__(self, filename):
        super(FileGroups, self).__init__()

        regexes = { "names": re.compile('^GROUP_NAMES\s*=\s*(.*)$'),
                    "quota": re.compile('^GROUP_QUOTA_([\w\.]+)\s*=\s*(\d+)$'),
                    "prio": re.compile('^GROUP_PRIO_FACTOR_([\w\.]+)\s*=\s*([\d\.]+)$'),
                    "surplus": re.compile('^GROUP_ACCEPT_SURPLUS_([\w\.]+)\s*=\s*(\w+)$'),
                  }
        grps = {}
        try:
            fp = open(filename, "r")
        except IOError, e:
            log.error("Error opening %s: %s", filename, e)
            sys.exit(1)

        for line in (x.strip() for x in fp if x and not re.match('^\s*#', x)):
            for kind, regex in regexes.items():
                if not regex.match(line):
                    continue

                if kind == "names":
                    group_names = regex.match(line).group(1).replace(' ','').split(',')
                else:
                    grp, val = regex.match(line).groups()
                    if not grps.get(grp):
                        grps[grp] = {}
                    grps[grp][kind] = val
        fp.close()
        for grp in group_names:
            p = grps[grp]
            self.add_group(grp, p["quota"], p["prio"], p["surplus"])

        if self.check_tree():
            log.error("Invalid group configuration found")
            sys.exit(1)




g = FileGroups("test.cfg")
d = DBGroups("atlas_group_quotas", host="localhost")



# for x in g:
#     print g[x]
# print g["group_cvmfs"]

y = Groups()

y.add_group("group_alpha", 124, 2.1, False)
y.add_group("group_beta", 11, 7.1, False)
y.add_group("group_alpha.gamma.delta", 15, 2.0, 1)
y.add_group("group_alpha.gamma", 15, 2.0, 1)

print g















