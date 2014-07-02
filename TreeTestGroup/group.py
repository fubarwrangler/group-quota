#!/usr/bin/python

# *****************************************************************************
#	A tree of scheduling groups. Leaf nodes are groups where jobs are
#	actually submitted, mid-level nodes set limits on the surplus-sharing
#	abilities of this tree of groups.
#
# *****************************************************************************

import sys
import MySQLdb
import logging

############################ VARIABLES ############################

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

# MySQL variable getter
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
	
      # Check if parent has surplus flag, for future use  
      def check_parent_surplus(self):
	    if self.parent.accept_surplus == 1:
	      return True
	    else:
	      return False
        
      def __iter__(self):
	      return iter(self.walk())
	  
      def __str__(self):
	      if self.name != '<root>': # Root has no values in table
		return '%s: quota %d, surplus %s' % \
		      (self.name, self.quota, self.accept_surplus)
	      else:
		return '%s' % \
		      (self.name)