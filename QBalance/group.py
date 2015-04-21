#!/usr/bin/python

# *****************************************************************************
# Group class used for Group creation, and eventual tree creation.
#
# Uses the atlas_group_quotas MySQL table to initialize the groups and
# dynamically populate the tree structure. When used with test.py, analyzes
# current and previous group queue amounts to determine accept_surplus flags.
# *****************************************************************************
#
# Includes script to query the MySQL database for the group_names and populate
# the necessary fields accordingly. The tree is created using the current '.'
# divider to separate parent from child in the group_name field.
# Those without a '.', are children of the root node.
#
# 1. Query MySQL database and populate the group_list
# 2. Sort the list and begin with the first entry
# 3. Populate the tree with a backtrack algorithm
# 4. Added a function to traverse the tree and update the data table's surplus
#    values based upon the surplus check analysis
#
# Added Group Functions:
#               tree_creation(self, cur, con):  creates the tree, for analysis
#               enable_surplus_changes(self, cur, con): updates the data table
#               no_recent_surplus_change(name, cur): checks for recent surplus switch
#               (Helper methods) -- aquire_groups, get_surplus, set_surplus
#
# By: Mark Jensen -- mvjensen@rcf.rhic.bnl.gov -- 6/13/14 *updated 7/8/14
#
# *****************************************************************************
import sys
import MySQLdb
import logging
import datetime
import config as c

# ########################## LOGGING INFO ###########################

logfile = "/home/mvjensen/dynamicgroups/TreeTestGroup/atlasSurplus.log"

logging.basicConfig(format="%(asctime)-15s (%(levelname)s) %(message)s",
                    filename=None if '-d' in sys.argv else logfile,
                    level=logging.DEBUG if '-d' in sys.argv else logging.INFO)

log = logging.getLogger()


# ######################### HELPER METHODS ##########################
# Populates a list with the groups in the database
def aquire_groups(con):
    cur = con.cursor()
    cur.execute("SELECT %s FROM %s" % (c.group_name, c.dbtable))
    data = cur.fetchall()
    cur.close()
    return sorted([i[0] for i in data])


def get_surplus(name, cur):
    cur.execute(c.get_Mysql_Val % (c.accept_surplus, c.dbtable, c.group_name, name))
    value = cur.fetchone()[0]
    return value


# USED FOR CHECKING WHETHER THE SURPLUS FLAG HAS BEEN FLIPPED IN THE LAST HOUR
# PREVENTS FLAPPING
def no_recent_surplus_change(name, cur):
    cur.execute(c.get_Mysql_Val % (c.last_surplus_update, c.dbtable, c.group_name, name))
    recent_surplus_time = cur.fetchone()[0]
    current_time = datetime.datetime.now()

    diff = current_time - recent_surplus_time
    hours, rest = divmod(diff.days*86400 + diff.seconds, 3600)
    # HOURS NOW = TIME DIFFERENCE ROUNDED DOWN TO THE HOUR
    if hours >= 1:
        return True         # NO RECENT SURPLUS CHANGES, ABLE TO CHANGE
    else:
        return False        # RECENT CHANGES, WAIT UNTIL ONE HOUR PASSES TO CHANGE


def set_surplus(name, value, cur, con):
    check = get_surplus(name, cur)
    no_recent_switch = no_recent_surplus_change(name, cur)
    if (check != value):
        if no_recent_switch:
            log.info("")
            log.info("Group: %s, Last switch greater than one hour ago, switch allowed", name)
            log.info("###########################################################################")
            log.info("######### Changing surplus of %s from %d to %d #########", name, check, value)
            log.info("###########################################################################")
            cur.execute(c.set_Mysql_surplus % (c.dbtable, c.accept_surplus, value,
                                               c.group_name, name))
            con.commit()
            cur.execute(c.set_Mysql_last_surplus_update % (c.dbtable, c.last_surplus_update,
                                                           c.group_name, name))
            con.commit()
        else:
            log.info("")
            log.info("######### Group: %s, surplus change is allowed, however, last change #########", name)
            log.info("######### less than one hour ago. Switch cancelled to prevent flapping #########")


###################################################################
# Group Object for group creation and tree formulation
class Group(object):
    def __init__(self, name):

        self.name = name
        self.queue = 0
        self.weight = None
        self.accept_surplus = None
        self.threshold = None

        # ### FOR TREE ####
        self.parent = None
        self.children = {}
        ###################

        if name != '<root>':  # IF ROOT, NO VALUES
            try:
                con = MySQLdb.connect(host=c.dbhost, user=c.dbuser, passwd=c.dbpass, db=c.database)
            except MySQLdb.Error as E:
                log.error("Error connecting to database: %s" % E)
                return None

            cur = con.cursor()

            cur.execute('SELECT %s, %s, %s FROM %s WHERE %s="%s"' %
                        (c.weight, c.accept_surplus, c.threshold, c.dbtable, c.group_name, name))
            self.weight, self.accept_surplus, self.threshold = cur.fetchall()

            cur.close()
            con.close()

    def add_child(self, name):
        # Add a child node to this one, setting it's parent pointer
        child = Group(name)
        child.parent = self
        self.children[name] = child
        return child  # Return child node for tree creation node pointer

    # Recursively iterate through all lower nodes in the tree
    def walk(self):
        if not self.children:
                return
        for x in self.children.values():
            yield x
            for y in x.walk():
                yield y

    # Return group by name
    def get_by_name(self, name):
        if self.name == name:
            return self
        for x in self.walk():
            if name == x.name:
                        return x
        raise Exception("No group %s found" % name)

    def __iter__(self):
        return iter(self.walk())

    def __str__(self):
        if self.name != '<root>':  # Root has no values in table
            return '%s: quota: %d, weight: %d, surplus: %s, threshold: %d' % \
                   (self.name, self.quota, self.weight, self.accept_surplus, self.threshold)
        else:
            return '%s' % (self.name)

    # Creates Group tree, Returns root node. Generated generically based on "." placement
    def tree_creation(self, con):
        current_node = self         # Set node to use as pointer to root
        prefix = None               # prefix  for parent/child identification
        for x in aquire_groups(con):
            if '.' not in x:          # No '.' denotes tier 1 group
                current_node = self     # Set current current_node to root current_node
                current_node = current_node.add_child(x)        # add child and adjust pointer
                prefix = x              # Set new prefix
            elif x.startswith(prefix):
                prefix = x              # Update prefix
                current_node = current_node.add_child(prefix)  # add and adjust
            else:
                # Used to backtrack if prefix not recognized
                while not x.startswith(prefix) & (prefix != '<root>'):
                    current_node = current_node.parent    # Backtrack
                    prefix = current_node.name            # Update prefix
                current_node = current_node.add_child(x)        # add and adjust
                prefix = x                              # Update prefix
        return self

    # Traverse the constructed group tree and update accept_surplus values in the table, if needed
    def enable_surplus_changes(self, cur, con):
        def child_walk(node):
            if node is not None:
                if node.parent is not None:
                    set_surplus(node.name, node.accept_surplus, cur, con)
                for n in node.children.values():
                    child_walk(n)
        child_walk(self)
