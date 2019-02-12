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

DBHOST = "rcfdb1.rcf.bnl.gov"
DBUSER = "db_query"
DB = "t3_groups"

TMP_FILE = '/etc/condor/tmpPolicyConfig'
CONFIG_PATH = '/etc/condor/tier3.usermap'

logging.basicConfig(filename='/tmp/htcondor-policy.log', level=logging.INFO,
                    format="%(asctime)-15s (%(levelname)-7s) %(message)s")
log = logging.getLogger()


def get_group_data():

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


def write_file(path, data):
    with open(path, 'w') as fp:
        print >> fp, "# =============================================="
        print >> fp, "# Policy map for Tier-3 Institution membership"
        print >> fp, "# ==============================================\n"

        for user, group in data:
            print >> fp, "* %s %s" % (user, group)
        print >> fp, "* /.*/ group_atlas.tier3.general\n"


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
    except Exception:
        log.exception("Error occured")
