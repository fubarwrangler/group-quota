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


# Get all parent groups of a group (separator is ".")
def get_parents(x):
    if noparent:
        return []
    return [".".join(x.split(".")[:-i]) for i in range(1, x.count(".") + 1)]

# Execute database command, or list of commands, and die if something goes wrong
def db_execute(command, database="group_quotas", host="localhost",
                        user="atlas_update", p="XPASSX"):
    try:
        conn = MySQLdb.connect(db=database, host=host, user=user, passwd=p)
        dbc = conn.cursor()
    except MySQLdb.Error, e:
        print "DB Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    try:
        if hasattr(command, '__iter__'):
            dbc.execute("START TRANSACTION")
            for c in command:
                dbc.execute(c)
            dbc.execute("COMMIT")
        else:
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
    groups = db_execute("SELECT group_name,quota,priority,accept_surplus FROM "
                        "atlas_group_quotas ORDER BY group_name", user="db_query")
    print 'There are %d groups' % len(groups)
    longest = max(len(x[0]) for x in groups)
    print 'Group ' + ' ' * (longest - 6) + '\tQuota\tPriority\tAccept_Surplus'
    print '------' + ' ' * (longest - 6) + '\t-----\t--------\t--------------'
    for g in groups:
        print '%s %s\t%d\t%.1f\t\t%s' % \
            (g[0], ' ' * (longest - len(g[0])), g[1], g[2], bool(g[3]))


def usage():
    print 'Usage: %s [-l] | [[-e group] [-q quota]|[-i interval]]' % sys.argv[0]
    print '  -l	Print a list of current groups/quotas'
    print '  -e	Edit quotas (needed by -g/-q options)'
    print '  -f	Forces changes to be made, no output (for scripting)'
    print '  -q	Specify new quota (must be positive integer)'
    print '  -p	Parent disable, do not add/subtract from parent groups'
    print '  -i	Specify difference from current value (+/- integer)'
    print '  -h	Shows this help screen'


# Write changes to db, asking for the user's approval unless force=True
def make_changes(oldquota, quota, group, d, force=False):

    query = 'UPDATE atlas_group_quotas SET '
    query += 'quota=%d WHERE group_name="%s"'

    if not force:
        print 'You will be setting %s from %d --> %d (%d)' % \
            (group, d[group], quota, quota - d[group])
        for x in get_parents(group):
              print ' * (parent update)  %s from %d --> %d (%d)' % \
                    (x, d[x], d[x] + (quota - oldquota), (quota - oldquota))
        proceed = raw_input('Is this OK? [y/N]: ')
        if proceed.upper() != 'Y':
            print 'OK, bailing...'
            return False
        else:
            print 'OK, making changes...'

    dbcommands = [query % (quota, group)]
    for x in get_parents(group):
        dbcommands.append(query % (d[x] + (quota - oldquota), x))
    db_execute(dbcommands)
    return True

try:
    opts, args = getopt.getopt(sys.argv[1:], 'lhpfe:q:i:')
except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)

EDIT = False
group = None
newquota = None
diff = None
force = False
noparent = False
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
    if o == '-p':
        noparent = True


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
            oldquota = d[group]
            quota = newquota
        else:
            if d[group] + diff < 0:
                print 'Error, quotas must remain positive'
                sys.exit(1)
            oldquota = d[group]
            quota = d[group] + diff

        # Write the changes to the database
        make_changes(oldquota, quota, group, d, force)
else:
    usage()
