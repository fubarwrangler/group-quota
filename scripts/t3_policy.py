#!/usr/bin/python

import MySQLdb
from collections import defaultdict

DBHOST = "localhost"
DBUSER = "willsk"
DB = "t3groups"


def do_query():
    query = """
    SELECT u.name, i.group FROM t3users AS u
    JOIN institutes AS i ON u.affiliation=i.name
    """
    con = MySQLdb.connect(host=DBHOST, user=DBUSER, db=DB)
    cur = con.cursor()
    cur.execute(query)
    results = cur.fetchall()
    con.close()
    return results

groups = defaultdict(list)

for name, group in do_query():
    groups[group].append(name)

template = """
# Policy for {group}
VALID_MEMBER = $(VALID_MEMBER) || \\
( ( (TARGET.AcctGroup == "{group}") || (TARGET.AcctGroup == "{group}.long") ) && \\
  stringListMember(Owner, "{namelist}") )
"""

for group, userlist in groups.iteritems():
    print "# =============================================="
    print "# Condor Policy for Validating Group Memberships"
    print "# ==============================================\n"
    print template.format(group=group, namelist=",".join(userlist))
