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

# Group Object for group creation and tree formulation
class Group(object): 
      def __init__(self, name):
	
	  self.name = name
	  self.quota = None
	  self.accept_surplus = None
	  
	  #### FOR TREE ####
	  self.parent = None
	  self.children = {}
	  ###################	  
	  
	  if name != '<root>': # IF ROOT, NO VALUES
	    try:
		con = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpass,
				      db=database)
	    except MySQLdb.Error as E:
		log.error("Error connecting to database: %s" % E)
		return None
	    cur = con.cursor()
	    # OBTAIN QUOTA
	    cur.execute(get_Mysql_Val % (quota, group_name, name))
	    self.quota = cur.fetchone()[0]
	    # OBTAIN SURPLUS
	    cur.execute(get_Mysql_Val % (accept_surplus, group_name, name))
	    self.accept_surplus = cur.fetchone()[0]
	    
	    cur.close()
	    con.close()	
	
      def add_child(self, name):
	      # Add a child node to this one, setting it's parent pointer
	      child = Group(name)
	      child.parent = self
	      self.children[name] = child
	      return child # Return child node for tree creation node pointer
	    
      def walk(self):
	      # Recursively iterate through all lower nodes in the tree
	      if not self.children:
		  return
	      for x in self.children.values():
		  yield x
		  for y in x.walk():
		      yield y
		    
      def get_by_name(self, name):
	      if self.name == name:
		  return self
	      for x in self.walk():
		  if name == x.name:
		      return x
	      raise Exception("No group %s found" % name)
	
      # NOT CODED, TODO	  
      #def check_parent_surplus(self, name):
      #      return name
      #  
      
      def __iter__(self):
	      return iter(self.walk())
	  
      def __str__(self):
	      if self.name != '<root>': # Root has no values in table
		return '%s: quota %d, surplus %s' % \
		      (self.name, self.quota, self.accept_surplus)
	      else:
		return '%s' % \
		      (self.name)

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
    #test = tree.get_by_name(group_list[4])
    #print test

