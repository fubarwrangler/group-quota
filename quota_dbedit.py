#!/usr/bin/python

# Desc: Program to interface with the the condor group quota database with
#       the ability to edit quotas on the command line (handy for scripting
#       changes to the quotas)
# Note: Needs to be run from a machine that has access to database.rcf.bnl.gov
#
# By: William Strecker-Kellogg -- willsk@bnl.gov
#
# 10/18/10 -- first version
# 12/6/10  -- restructured the code and add an incremental option '-i'
# 12/14/10 -- fixed bug where -q 0 wouldn't work (fixed by compare w/ None)
# 1/24/12  -- Minor aesthetic fixes and fix for heirarchical group database


import sys
import getopt
import MySQLdb


# Execute database command, or list of commands, and die if something goes wrong
def db_execute(command, database="linux_farm", host="localhost", user="atlas_update", p="xxx"):
    try:
        conn = MySQLdb.connect(db=database, host=host, user=user, passwd=p)
        dbc = conn.cursor()
    except MySQLdb.Error, e:
        print "DB Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    try:
        dbc.execute(command)
    except MySQLdb.Error, e:
        print "DB Error %d: %s" % (e.args[0], e.args[1])
        dbc.close()
        conn.close()
        sys.exit(1)
    db_data = dbc.fetchall()
    dbc.close()
    conn.commit()
    return db_data


# Show a table of the quota information
def print_quotas():
    groups = db_execute("SELECT group_name,quota,priority,accept_surplus FROM atlas_group_quotas ORDER BY group_name", user="db_query", p="")
    print 'There are %d groups' % len(groups)
    longest = max(len(x[0]) for x in groups)
    print groups
    print 'Group:' + ' ' * longest + '\tQuota\tPriority\tAccept_Surplus'
    print '------' + ' ' * longest + '\t-----\t--------\t--------------'
    for g in groups:
        print '%s:%s\t%d\t%.1f\t\t%s' % \
        (g[0], ' ' * (longest - len(g[0])), g[1], g[2], bool(g[3]))


def usage():
    print 'Usage: %s [-l] | [[-e group] [-q quota]|[-i interval]]' % sys.argv[0]
    print '  -l	Print a list of current groups/quotas'
    print '  -e	Edit quotas (needed by -g/-q options)'
    print '  -f	Forces changes to be made, no output (for scripting)'
    print '  -q	Specify new quota (must be positive integer)'
    print '  -i	Specify difference from current value (+/- integer)'
    print '  -h	Shows this help screen'


# Write changes to db, asking for the user's approval unless force=True
def make_changes(quota, group, d, force=False):

    query = 'UPDATE atlas_group_quotas SET '
    query += 'quota=%d WHERE group_name="%s"' % (quota, group)

    if not force:
        print 'You will be setting %s from %d --> %d' % (group, d[group], quota)
        proceed = raw_input('Is this OK? [y/N]: ')
        if proceed.upper() != 'Y':
            print 'OK, bailing...'
            return False
        else:
            print 'OK, making changes...'
    db_execute(query)
    return True

try:
    opts, args = getopt.getopt(sys.argv[1:], 'lhfe:q:i:')
except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)

EDIT = False
group = None
newquota = None
diff = None
force = False
for o, a in opts:
    if o == '-l':
        print_quotas()
        sys.exit(0)
    if o == '-e':
        group = a
        EDIT = True
    if o == '-q':
        newquota = int(a)
    if o == '-i':
        diff = int(a)
    if o == '-f':
        force = True

if newquota and diff:
    print 'Please specify only a new quota or a difference, not both'
    EDIT = False


if EDIT and group and (newquota is not None or diff is not None):

    # Gather information on groups and their quotas
    groups = db_execute("SELECT group_name,quota,priority,accept_surplus FROM atlas_group_quotas ORDER BY group_name", user="db_query", p="")
    names = [x[0] for x in groups]
    quotas = [x[1] for x in groups]
    d = dict(zip(names, quotas))

    if group not in d:
        print 'Error, group %s not in database' % group
    else:
        # Get new quota from newquota or diff
        if newquota is not None:
            quota = newquota
        else:
            if d[group] + diff < 0:
                print 'Error, quotas must remain positive'
                sys.exit(1)
            quota = d[group] + diff

        # Write the changes to the database
        make_changes(quota, group, d, force)
else:
    usage()
