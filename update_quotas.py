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

file_handler = logging.FileHandler(LOGFILE)
file_handler.setLevel(LOGLEVEL)
file_handler.setFormatter(frmt)

log.addHandler(file_handler)

# Needed to run reconfig command below
os.environ['CONDOR_CONFIG'] = '/etc/condor/condor_config.atlas'

class Group(object):
    def __init__(self, name='', quota='0', prio='0.0', auto='FALSE'):
        self.name = name
        self.quota = quota
        self.prio = prio
        self.auto = auto
    # so we can print a group object in the proper format
    def __str__(self):
        msg  = '\n'
        msg += 'GROUP_QUOTA_%s = %s\n' % (self.name, self.quota)
        msg += 'GROUP_PRIO_FACTOR_%s = %s\n' % (self.name, self.prio)
        msg += 'GROUP_AUTOREGROUP_%s = %s\n' % (self.name, self.auto)
        return msg

    def __eq__(self, other):
        if other.name == self.name and other.quota == self.quota and other.prio == self.prio and other.auto == self.auto:
            return True
        else:
            return False
    def __ne__(self, other):
        if other.name != self.name or other.quota != self.quota or other.prio != self.prio or other.auto != self.auto:
            return True
        else:
            return False

class Groups(object):

    def __init__(self):
        self.groups = []

    def read(self):
        raise AttributeError("Must use derived class")

    def get_names(self):
        return [x.name for x in self.groups]

    def __str__(self):
        return "GROUP_NAMES = %s\n" % ', '.join(self.get_names())

    def __iter__(self):
        return iter(self.groups)

    def __getitem__(self, n):
        return self.groups[n]

    def __len__(self):
        return len(self.groups)

class DBGroups(Groups):

    def __init__(self, database, host, user):
        Groups.__init__(self)
        try:
            con = MySQLdb.connect(db=database,host=host,user=user,connect_timeout=30)
            dbc = con.cursor()
            dbc.execute("SELECT group_name,quota,priority,auto_regroup "
                        "FROM atlas_group_quotas ORDER BY group_name")
        except MySQLdb.Error, e:
            log.error("DB Error %d: %s" % (e.args[0], e.args[1]))
            sys.exit(1)
        except Exception, e:
            log.error("Exception: %s" % e)
            sys.exit(1)

        self.db_input = dbc.fetchall()

        dbc.close()
        con.close()

    # Read the groups from the database and load them into 'groups'
    def read(self):
        for db_row in self.db_input:
            name = db_row[0]
            quota = int(db_row[1])
            prio = float(db_row[2])
            auto = db_row[3]

            if not re.match('^group_\w+$', name):
                log.error('Bad groupname "%s", exiting', name)
                sys.exit(1)
            if not re.match('^(TRUE)|(FALSE)$', auto):
                log.error('Bad auto_regroup "%s", exiting', auto)
                sys.exit(1)
            self.groups.append(Group(name, quota, prio, auto))


class CfgGroups(Groups):

    def __init__(self, filename):
        Groups.__init__(self)
        self.filename = filename

    # Read the groups from the current file and load them into 'groups'
    def read(self):
        try:
            fp = open(self.filename)
        except:
            log.error('Failed to open quota file "%s"' % self.filename)
            sys.exit(1)
        lines = []
        found_names = False
        grp_dict = {}
        name_fmt = re.compile('^GROUP_NAMES\s*=\s*(.*)$')
        quota_fmt = re.compile('^GROUP_QUOTA_(\w+)\s*=\s*(\d+)$')
        prio_fmt = re.compile('^GROUP_PRIO_FACTOR_(\w+)\s*=\s*([\d\.]+)$')
        auto_fmt = re.compile('^GROUP_AUTOREGROUP_(\w+)\s*=\s*(\w+)$')
        for line in (x for x in fp if not re.match('^\s*#', x)):
            if name_fmt.match(line):
                group_names = name_fmt.match(line).group(1).replace(' ','').split(',')
                for n in group_names:
                    grp_dict[n] = {}
                found_names = True
            if found_names:
                if quota_fmt.match(line):
                    grp_dict[quota_fmt.match(line).group(1)]['quota'] = int(quota_fmt.match(line).group(2))
                if prio_fmt.match(line):
                    grp_dict[prio_fmt.match(line).group(1)]['prio'] = float(prio_fmt.match(line).group(2))
                if auto_fmt.match(line):
                    grp_dict[auto_fmt.match(line).group(1)]['auto'] = auto_fmt.match(line).group(2)

        for name in sorted(grp_dict.keys()):
            g = grp_dict[name]
            self.groups.append(Group(name, g['quota'], g['prio'], g['auto']))
        fp.close()


def send_email(address):

    log.info('Sending mail to "%s"...' % address)
    body = \
"""
Info: condor03 has detected a change in the ATLAS group quota
database; see the following links for a detailed description of the changes
made and who made them:

https://webdocs.racf.bnl.gov/Facility/LinuxFarm/cgi-bin/group_quota.py
https://webdocs.racf.bnl.gov/Facility/LinuxFarm/atlas_groupquota.log

Receipt of this message indicates that condor has been successfully
reconfigured to use the new quotas indicated on the page above.
"""
    msg = MIMEText(body)
    msg['From'] = "root@condor03"
    msg['To'] = address
    msg['Subject'] = "Group quotas changed"
    try:
        smtp_server = smtplib.SMTP('rcf.rhic.bnl.gov', 25)
        smtp_server.sendmail(msg['From'], msg['To'], msg.as_string())
    except:
        log.error('Problem sending mail, no message sent')
        return 1
    return 0

# *****************************************************************************

parser = optparse.OptionParser()
parser.add_option("-m", "--mail", action="store", dest="email",
                  help="Send email to address given here when a change is made")
parser.add_option("-r", "--reconfig", action="store_true", default=False,
                  help="Issue a condor_reconfig after a change is detected")
options, args = parser.parse_args()

db_groups = DBGroups(database="linux_farm", host="database.rcf.bnl.gov", user="db_query")
file_groups = CfgGroups(filename=QUOTA_FILE)

db_groups.read()
file_groups.read()

if len(db_groups) == 0:
    log.error("Got empty response from DB, abort")
    sys.exit(1)

# Could use more elegant set module and check XOR, but involves an extra dependancy
# Lol, no it doesn't
diff = 0
for db_group in db_groups:
    # Uses __eq__ to check for group equality
    if db_group in file_groups:
        pass
    else:
        diff = 1
if len(db_groups) != len(file_groups):
    diff = 1

# Get out now if nothing changed
if diff == 0:
    log.debug('No Database Change...')
    sys.exit(0)

# 1. Open temporary file --> Write Changed quota file to temp file
# 2. If backup exists, overwrite it with copy of current file
# 3. Overwrite current file w/ temp file
try:
    # Needs to be on same filesystem to allow hardlinking that goes on when
    # os.rename() is called, else we get a 'Invalid cross-device link' error
    tmpname = tempfile.mktemp(suffix='grpq', dir=os.path.dirname(QUOTA_FILE))
    tmpfile = open(tmpname, 'w')
except IOError:
    log.error('Failed opening temporary file')
    sys.exit(1)

header = """# -----------------------------------------------------
#  This file is automatically generated -- DO NOT EDIT
# -----------------------------------------------------

"""

try:
    tmpfile.write(header)
    tmpfile.write(str(db_groups))
    for grp in db_groups:
        tmpfile.write(str(grp))
    tmpfile.close()
except:
    log.error('Failed writing to temporary file')
    # FIXME: can this throw an exception?
    os.unlink(tmpname)
    sys.exit(1)

# This will overwrite the backup
shutil.copy2(QUOTA_FILE, QUOTA_BACKUP)

# XXX: Python-docs say this is gauranteed to be atomic
os.rename(tmpname, QUOTA_FILE)

log.info('Quota file updated with new values')

# Do a reconfig, and send mail before we exit
if options.reconfig:
    if subprocess.call('/usr/sbin/condor_reconfig') != 0:
        log.error('Problem with condor_reconfig, returned nonzero')
        sys.exit(1)
    log.info('Reconfig successful...')
else:
    log.info('No reconfig done...')

if options.email:
    sys.exit(send_email(options.email))
else:
    log.info('Not sending mail...')

sys.exit(0)
