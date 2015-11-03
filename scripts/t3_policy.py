#!/usr/bin/python
# ****************************************************************************
# Script to write a HTCondor policy macro that enforces accountinggroup
# membership from the database
# ****************************************************************************

import os
import os.path
import hashlib
import logging
import subprocess

import MySQLdb

from collections import defaultdict

DBHOST = "rcfdb1.rcf.bnl.gov"
DBUSER = "db_query"
DB = "t3_groups"

TMP_FILE = '/etc/condor/tmpPolicyConfig'
CONFIG_PATH = '/etc/condor/config.d/50_valid_member'

logging.basicConfig(filename='/tmp/htcondor-policy.log', level=logging.INFO,
                    format="%(asctime)-15s (%(levelname)-7s) %(message)s")
log = logging.getLogger()


def get_group_data():

    def do_query():
        query = """
        SELECT u.name, i.group FROM t3users AS u
        JOIN institutes AS i ON u.affiliation=i.name
        """
        con = MySQLdb.connect(host=DBHOST, user=DBUSER, db=DB, connect_timeout=20)
        cur = con.cursor()
        cur.execute(query)
        results = cur.fetchall()
        con.close()
        return results

    groups = defaultdict(list)

    for name, group in do_query():
        if group != 'group_atlas.general':
            groups[group].append(name)

    return groups


def write_file(path, data):

    template = """
# Policy for {group}
VALID_MEMBER = $(VALID_MEMBER) || \\
( ( (TARGET.AcctGroup == "{group}") || (TARGET.AcctGroup == "{group}.long") ) && \\
  stringListMember(Owner, "{namelist}") )
"""
    with open('/etc/condor/tmpPolicyConfig', 'w') as fp:
        print >> fp, "# =============================================="
        print >> fp, "# Condor Policy for Validating Group Memberships"
        print >> fp, "# ==============================================\n"
        print >> fp, 'VALID_MEMBER = (TARGET.AcctGroup == "group_atlas.general")\n'

        for group, userlist in data.iteritems():
            print >> fp, template.format(group=group, namelist=",".join(userlist))


def hash_file(path):
    m = hashlib.sha1()
    try:
        with open(path) as fp:
            m.update(fp.read())
    except EnvironmentError:
        return ''
    return m.digest()


def do_main():
    groupmap = get_group_data()
    write_file(TMP_FILE, groupmap)

    # Update config directory and run reconfig if changed path
    if hash_file(TMP_FILE) != hash_file(CONFIG_PATH) and os.path.getsize(TMP_FILE) > 0:
        os.rename(TMP_FILE, CONFIG_PATH)
        with open(os.devnull, 'w') as null:
            subprocess.check_call(['/usr/sbin/condor_reconfig'], stdout=null, stderr=null)
        log.info("Updated config file and reconfigured condor...")
    else:
        os.remove(TMP_FILE)


if __name__ == "__main__":
    try:
        do_main()
    except:
        log.exception("Error occured")
