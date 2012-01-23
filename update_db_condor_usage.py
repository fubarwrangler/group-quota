#!/usr/bin/python

# Desc: Simple script to read the condor usage information from the atlas central 
#       manager and record it in the atlas_group_quota database on database (cronjob)
# 
# By: William Strecker-Kellogg -- willsk@bnl.gov
#
# CHANGELOG:
# 7/29/10: v1.0 put into production
# 8/3/10: revised to not use RACF_Group, by using the hidden regexp() feature to match group names
# 10/29/10: revised to use only one call to condor_status, much more efficient

# NOTE: Needs the (empty) file /etc/condor/condor_config to exist!!
#       This script works in conjunction with /var/www/cgi-bin/group_quota.py on
#       farmweb01, which serves as a web interface to edit this database.

import commands, sys, re, time
import MySQLdb

# Execute database command, or list of commands, and die if something goes wrong
def db_execute(command, database="linux_farm", host="database.rcf.bnl.gov", user="condor_update", p="XPASSX"):
  try:
    conn = MySQLdb.connect(db=database,host=host,user=user,passwd=p)
    dbc = conn.cursor()
  except MySQLdb.Error, e:
    print "DB Error %d: %s" % (e.args[0], e.args[1])
    sys.exit(1)
  try:
    if (type(command) is list or type(command) is tuple) and len(command) > 0:
      for item in command:
        dbc.execute(item)
    elif type(command) is str:
      dbc.execute(command)
    else:
      raise ValueError
  except MySQLdb.Error, e:
    print "DB Error %d: %s" % (e.args[0], e.args[1])
    dbc.close()
    sys.exit(1)
  except ValueError:
    print 'Invalid command type, nothing sent to db sent to db'
    dbc.close()
    sys.exit(1)
  db_data = dbc.fetchall()
  conn.close()
  return db_data

# get groups from database
db_groups = [x[0] for x in db_execute("SELECT group_name FROM atlas_group_quotas")]
if db_groups == []:
  print 'Error, no groups in database?'
  sys.exit(1)

# get info from condor
active = dict(zip(db_groups, [0]*len(db_groups)))
data = commands.getoutput("condor_status -pool condor03.usatlas.bnl.gov:9660 -constraint 'TARGET.AccountingGroup =!= UNDEFINED' -format '%s\n' AccountingGroup | sed 's/\..*//g' | sort | uniq -c").split('\n')

# Populate "active" dict with info
data = [x.lstrip() for x in data]
for j in data:
  try:
    (num, grp) = re.split(' ', j)
  except ValueError:
    print 'Got strange feedback from command'
    sys.exit(1)
  if grp in db_groups:
    if num.isdigit():
      active[grp] = int(num)

# Write to db
qstr = 'UPDATE atlas_group_quotas SET busy = %d WHERE group_name = "%s"'
queries = [qstr % (active[x], x) for x in active.keys()]
queries.append('UPDATE atlas_group_quotas SET last_change = %d' % int(time.time()))

db_execute(queries)


