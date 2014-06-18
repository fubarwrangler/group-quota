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
import datetime
from group import Group

############################ VARIABLES ############################
# List of group names to eventually populate from Database
group_list = []

# List of leaf group names sorted by priority
priority_list = []

logfile = "/home/mvjensen/dynamicgroups/testlog.log"

# Database parameters
dbtable = 'atlas_group_quotas'
queue_log_table = 'queue_log'
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
amount_in_queue = 'amount_in_queue'
query_time = 'query_time'
surplus_threshold = 'surplus_threshold'



# MySQL variable getters and setters
get_Mysql_groups = 'SELECT %s FROM %s;'
get_Mysql_Val = 'SELECT %s FROM %s WHERE %s="%s"'
get_Mysql_queue_avg = 'SELECT AVG(%s) FROM %s WHERE TIMESTAMPDIFF(HOUR, %s, NOW()) < 1 AND %s="%s";'
get_Mysql_sorted_priority_list = 'SELECT %s FROM %s WHERE %s>0 ORDER BY %s DESC;'
set_Mysql_surplus = 'UPDATE %s SET %s=%d WHERE %s="%s";'

logging.basicConfig(format="%(asctime)-15s (%(levelname)s) %(message)s",
                    filename=None if '-d' in sys.argv else logfile,
                    level=logging.DEBUG if '-d' in sys.argv else logging.INFO)

#logging.basicConfig(filename=logfile, level=logging.INFO)

#logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    #format="(%(levelname)5s) %(message)s")
log = logging.getLogger()



### OPEN MySQL DATABASE FOR SCRIPT USE, CLOSE AT THE END###
try:
  con = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpass,
			db=database)
except MySQLdb.Error as E:
  log.error("Error connecting to database: %s" % E)
cur = con.cursor()
###################################################################

# Populates the group_list with the groups in the database
def aquire_groups():
  cur.execute(get_Mysql_groups % (group_name, dbtable))
  results = [i[0] for i in cur.fetchall()]
  for x in results:
    group_list.append(x)

# Populates the priority_list with the names of the tree leaves
def order_by_priority():
  # OBTAIN LIST OF GROUPS WITH PRIORITY > 0
  cur.execute(get_Mysql_sorted_priority_list % (group_name, dbtable, priority, priority))
  results = [i[0] for i in cur.fetchall()]
  for x in results:
    priority_list.append(x)
  
def get_priority_value(name):
  cur.execute(get_Mysql_Val % (priority, dbtable, group_name, name))
  value = cur.fetchone()[0]
  return value

# Gets the average queue amount for the group over the past hour
def get_average_hour_queue(name):
  cur.execute(get_Mysql_queue_avg % (amount_in_queue, queue_log_table, query_time, group_name, name))
  average = cur.fetchone()[0]
  return average

def get_threshold(name):
  cur.execute(get_Mysql_Val % (surplus_threshold, dbtable, group_name, name))
  value = cur.fetchone()[0]
  return value

def get_surplus(name):
  cur.execute(get_Mysql_Val % (accept_surplus, dbtable, group_name, name))
  value = cur.fetchone()[0]
  return value

def set_surplus(name, value):
  check = get_surplus(name)
  if check != value:
    log.info("######### Changing surplus of %s to %d #########", name, value)
    cur.execute(set_Mysql_surplus % (dbtable, accept_surplus, value, group_name, name))
    con.commit()
  

def surplus_check():
  mp_surp_flag = False
  order_by_priority()
  for x in priority_list:
    avg = get_average_hour_queue(x)
    thresh = get_threshold(x)
    log.info("Name: %s, Past hour Avg: %d, Thresh: %d", x, avg, thresh)
    # PYTHON SWITCH STATEMENT
    if get_priority_value(x) == 3.0:	# IF MULTICORE:
      if avg < thresh:
	mp_surp_flag = True
	log.info("Past hour average of %s below threshold.", x)
	set_surplus(x,1)
      else:
	#TODO CHECK FOR SPIKE
	mp_surp_flag = False
	log.info("Past hour average of %s above threshold.", x)
	set_surplus(x,0)
    elif get_priority_value(x) == 2.0:	# IF PRODUCTION LEAF
      if mp_surp_flag:
	log.info("Multi-processor accept_surplus is True, cannot alter accept_surplus.")
	set_surplus(x,0)
      else:
	if avg < thresh:
	  log.info("Multi-processor accept_surplus is False, and Past hour average of %s below threshold.", x)
	  set_surplus(x,1)
	else:
	  #TODO CHECK FOR SPIKE
	  log.info("Multi-processor accept_surplus is False, and Past hour average of %s above threshold.", x)
	  set_surplus(x,0)


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
        # Iterate and Print a tab indented tree to test 
        if not tree.children:
            print 'Parent: ' + str(tree.parent.name) + ', Group: ' + str(tree)
        else:
	  for x in tree.children.values():
            print 'Parent: ' + str(x.parent.name) + ', Group: ' + str(x)
            for y in x.walk():
	      if y.children:
		print '\tParent: ' + str(y.parent.name) + ', Group: ' + str(y)
	      else:
		if y.name == 'group_atlas.software':
		  print '\tParent: ' + str(y.parent.name) + ', Group: ' + str(y)
		else:
		  print '\t\tParent: ' + str(y.parent.name) + ', Group: ' + str(y) + ', Queue average in past hour: ' + str(get_average_hour_queue(y.name))


def do_main():
  log.info("!!atlas_group_quotas table surplus changes possible!!")
  surplus_check()
  cur.close()
  con.close()
  log.info("")

# To test
if __name__ == '__main__':
  try:
    sys.exit(do_main())
  except Exception:
    log.exception("Uncaught exception")
    sys.exit(1)
    #root = Group('<root>')
    #tree = tree_creation(root)
    #print ''
    #print 'Time: ' + str(datetime.datetime.now())
    #print_tree(tree)
    #print ''
    #surplus_check()
    #cur.close()
    #con.close()
    #print group_list
    #print ''
    #test = tree.get_by_name(group_list[5])
    #print 'test: ' + str(test)
    #check = test.check_parent_surplus()
    #print 'Parent: ' + str(test.parent.name) + ' has surplus = ' + str(check)
    #print ''
    #average = get_average_hour_queue(test.name)
    #print 'Average queue in last hour: ' + str(average)
