#!/usr/bin/python

# *****************************************************************************
# Script to query the MySQL database for the group_names and populate
# the necessary fields accordingly. The tree is created using the current '.'
# divider to separate parent from child in the group_name field. 
# Those without a '.', a children of the root node.
#
# 1. Query MySQL database and populate the group_list
# 2. Sort the list and begin with the first entry
# 3. Populate the tree with a backtrack algorithm
#
# By: Mark Jensen -- mvjensen@rcf.rhic.bnl.gov -- 6/13/14
#
# *****************************************************************************

import sys
import MySQLdb
import logging
from group import Group

############################ VARIABLES ############################
# List of group names to eventually populate from Database
group_list = []

# Database parameters
dbtable = 'atlas_group_quotas'
dbhost = 'old-db.rcf.bnl.gov'
database = 'atlas_demand'
dbuser = 'group_edit'
dbpass = 'atlas'

# Table Fields for ease of future modification in case they are changed
group_name = 'group_name'
quota = 'quota'
priority = 'priority'
accept_surplus = 'accept_surplus'
busy = 'busy'
last_update = 'last_update'

# MySQL variable getters
get_MySQL_groups = 'SELECT ' + group_name + ' FROM '+ dbtable
get_Mysql_Val = 'SELECT %s FROM '+ dbtable + ' WHERE %s="%s"'

###################################################################

# Populates the group_list with the groups in the database
def aquire_groups():
  try:
    con = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpass,
                              db=database)
  except MySQLdb.Error as E:
    log.error("Error connecting to database: %s" % E)
    return None
  cur = con.cursor()
  cur.execute(get_MySQL_groups)
  results = [i[0] for i in cur.fetchall()]
  for x in results:
    group_list.append(x)
    
# Creates Group tree, Returns root node
def tree_creation(root):
  aquire_groups()		# Populate group_list
  group_list.sort()		# Sort list
  current_node = root		# Set node to use as pointer to root
  prefix = None			# prefix  for parent/child identification
  for x in group_list:
    if '.' not in x: 		# No '.' denotes tier 1 group
      current_node = root	# Set current current_node to root current_node
      current_node = current_node.add_child(x)	# add child and adjust pointer
      prefix = x		# Set new prefix
    elif x.startswith(prefix):
      prefix = x		# Update prefix
      current_node = current_node.add_child(prefix) # add and adjust
    else:
      # Used to backtrack if prefix not recognized
      while not x.startswith(prefix) & (prefix != '<root>'):
	current_node = current_node.parent 	# Backtrack
	prefix = current_node.name 		# Update prefix
      current_node = current_node.add_child(x)	# add and adjust
      prefix = x				# Update prefix
  return root

def print_tree(tree):
        # Iterate and Print to test
        if not tree.children:
            print 'Parent: ' + str(tree.parent.name) + ', Group: ' + str(tree)
        for x in tree.children.values():
            print 'Parent: ' + str(x.parent.name) + ', Group: ' + str(x)
            for y in x.walk():
              print 'Parent: ' + str(y.parent.name) + ', Group: ' + str(y)

# To test
if __name__ == '__main__':
    root = Group('<root>')
    tree = tree_creation(root)
    print ''
    print_tree(tree)
    print ''
    print group_list
    print ''
    test = tree.get_by_name(group_list[4])
    print 'test: ' + str(test)
    check = test.check_parent_surplus()
    print 'Parent: ' + str(test.parent.name) + ' has surplus = ' + str(check)
    print ''
