#!/usr/bin/python
# ****************************************************************************
# Script to write a HTCondor long subgroups for T3
# ****************************************************************************

import logging
import MySQLdb

DBHOST = "rcfdb1.rcf.bnl.gov"
DBUSER = "db_query"
DB = "t3_groups"

logging.basicConfig(filename='/tmp/htcondor-policy.log', level=logging.INFO,
                    format="%(asctime)-15s (%(levelname)-7s) %(message)s")
log = logging.getLogger()


def get_group_data():

    def do_query():
        query = """SELECT group_name FROM groups"""
        con = MySQLdb.connect(host=DBHOST, user=DBUSER, db=DB, connect_timeout=20)
        cur = con.cursor()
        cur.execute(query)
        results = cur.fetchall()
        con.close()
        return results

    skip = ('group_atlas.general', 'group_atlas.panda', 'group_wisc', 'group_atlas')

    return set(x[0] for x in do_query()) - set(skip)


def do_main():
    groups = get_group_data()

    print '# Long subgroups...'
    print 'GROUP_NAMES = $(GROUP_NAMES), \\\n%s\n' % \
        ', \\\n'.join(x + '.long' for x in sorted(groups))

    for group in groups:
        print 'GROUP_QUOTA_DYNAMIC_%s.long = 0.2' % group


if __name__ == "__main__":
    try:
        do_main()
    except:
        log.exception("Error occured")
