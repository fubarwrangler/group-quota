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

# Spike multiplier used to multiply threshold and determine if queue spike is present
spike_multiplier = 2

# Rapid reduction modifier, to determine if the amount has decreased the necessary percentage
reduce_mod = .875 # Checks if the spike has dropped by 1/4

#logfile = "/home/mvjensen/dynamicgroups/testlog.log"

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
get_Mysql_queue_amounts = 'SELECT %s FROM %s WHERE TIMESTAMPDIFF(HOUR, %s, NOW()) < 1 AND %s="%s";'
get_Mysql_sorted_priority_list = 'SELECT %s FROM %s WHERE %s>0 ORDER BY %s DESC;'
set_Mysql_surplus = 'UPDATE %s SET %s=%d WHERE %s="%s";'

#logging.basicConfig(format="%(asctime)-15s (%(levelname)s) %(message)s",
                    #filename=None if '-d' in sys.argv else logfile,
                    #level=logging.DEBUG if '-d' in sys.argv else logging.INFO)

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="(%(levelname)5s) %(message)s")

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

# Returns a list of the queue amounts for the specified group over the past hour to analyze
def get_past_hour_queue_amounts(name):
  queue_amounts = []
  cur.execute(get_Mysql_queue_amounts % (amount_in_queue, queue_log_table, query_time, group_name, name))
  results = [i[0] for i in cur.fetchall()]
  for x in results:
    queue_amounts.append(x)
  return queue_amounts

# In order to account for the rapid depletion of a large spike occuring 
# without any necessary changes, only check the difference between the 
# first 8 of 12 entries in the last hour to ensure that a last minute spike 
# is not detected without the ability to decipher whether it is an issue or not.
def check_for_spike(name):
  
  
  #amounts = [5,40,0,180,14,178,88,188,0,166,999,160]		# For Debug
  #avg = reduce(lambda x, y: x + y, amounts) / len(amounts) 	# For Debug
  
  
  amounts = get_past_hour_queue_amounts(name)
  avg = get_average_hour_queue(name)	# Eventually passed variable
  spike_flag = False			# Initialize to False
  surplus_flag = False
  length = len(amounts)
  threshold = get_threshold(name) 	# Eventually passed variable
  
  
  ## For Debug purposes ##
  print ""
  print 'Checking spike for ' + name
  print 'AVERAGE: ' + str(avg) + ', THRESHOLD * 10: ' + str(threshold*10)
  #########################
  
  if avg < threshold*10: # Queue limit for spike check
    max_index = 0
    max_difference = 0
    limitCheck = threshold*spike_multiplier
    
    ## For Debug purposes ##
    y = 0
    for x in amounts:
      print 'Amount ' + str(y) + ': ' + str(x) 
      y += 1
    print ""
    #########################
    
    test = [x - amounts[i - 1] for i, x in enumerate(amounts)][1:]
    # Index used for testing
    index = test.index(max(test[0:7]))
    
    print 'MAX DIFFERENCE IN FIRST 8 VALUES: ' + str(max(test[0:7])) + ', at Amount time: ' + str(index+1)
    print 'Spike Threshold = ' + str(limitCheck)
    print ""
    
    # Check all values for a spike in order to allow a late spike to be checked before reacting to soon
    if max(test) < limitCheck: # if all values are too low, no need to do any extra work
      print 'NO POSSIBLE SPIKES FOUND'
      
    else:
      print  'POSSIBLE SPIKE IN LAST HOUR'
      spike_flag = True
      i = 0
      
      while i < 7:
	diff = amounts[i+1] - amounts[i]
	
	# Update max index and value
	if diff > max_difference:
	    max_index = i+1
	    max_difference = diff
	    
	# Percent increase can only be determined when not starting at zero
	if amounts[i] != 0: 
	  percent = round(float(diff)/float(amounts[i]), 4)
	  percent = percent * 100
	  print 'Difference between ' + str(i) + ' and ' + str(i+1) + ' = ' + str(diff) + ', a ' + str(percent) + '% change.'
	  
	  if percent < 0:
	    print 'DECREASE DETECTED'
	    
	  elif percent >= 500:
	    if amounts[i+1] >= limitCheck:
	      print 'SPIKE DETECTED, DETERMINING RAPID REDUCTION'
	      print 'spike = ' + str(amounts[max_index]) + ', .875 * spike = ' + str(amounts[max_index]*reduce_mod) + ', most recent value = ' + str(amounts[length-1]) 
	      if amounts[max_index]*reduce_mod > amounts[length-1]:
		print 'SPIKE DECREASING NORMALLY, NO CHANGE NEEDED'
		surplus_flag = False
	      else:
		print 'SPIKE NOT DECREASING NORMALLY, SWITCH ON ACCEPT SURPLUS IF POSSIBLE'
		surplus_flag = True
	    else:
	      print 'HIGH PERCENTAGE, LOW VALUE. NOT A SPIKE'
	  
	  else:
	    print 'NOT A SPIKE'
	 
	## STARTING AT ZERO DIFFERENCE MUST BE GREATER THAN SPIKE THRESHOLD
	else: 
	  print 'Since previous value 0, Difference between ' + str(i) + ' and ' + str(i+1) + ' = ' + str(diff)
	  if diff > limitCheck:
	    print 'SPIKE DETECTED, DETERMINING RAPID REDUCTION'
	    print 'spike = ' + str(amounts[max_index]) + ', .875 * spike = ' + str(amounts[max_index]*reduce_mod) + ', most recent value = ' + str(amounts[length-1]) 
	    if amounts[max_index]*reduce_mod > amounts[length-1]:
	      print 'SPIKE DECREASING NORMALLY, NO CHANGE NEEDED'
	      surplus_flag = False
	    else:
	      print 'SPIKE NOT DECREASING NORMALLY, SWITCH ON ACCEPT SURPLUS IF POSSIBLE'
	      surplus_flag = True
	  else:
	    print 'NOT A SPIKE'
	i += 1
	
      print 'Max diff = ' + str(max_difference)
      
  else:
    print 'Queue amount exceeds spike check threshold, enable flag if possible'
    
  # if SPIKE NOT DECREASING NORMALLY, SWITCH ON ACCEPT SURPLUS IF POSSIBLE
  if surplus_flag:
    print ("Switching on accept surplus for %s", name)
    #set_surplus(name,1)
    
  return spike_flag


def surplus_check():
  mp_surp_flag = False
  order_by_priority()
  for x in priority_list:
    avg = get_average_hour_queue(x)
    thresh = get_threshold(x)
    log.info("Name: %s, Past hour Avg: %d, Thresh: %d", x, avg, thresh)
    # PYTHON SWITCH STATEMENT
    
    
    if get_priority_value(x) == 3.0:	# IF MULTICORE:
      # if TODO CHECK FOR SPIKE FIRST:
      #if check_for_spike(x):
	#mp_surp_flag = True
	#log.info("Multi-core queue spike detected in past hour.")
      if avg < thresh:
	mp_surp_flag = False
	log.info("Past hour average of %s < threshold.", x)
	set_surplus(x,0)
      else:
	mp_surp_flag = True
	log.info("Past hour average of %s > threshold. accept_surplus set to true", x)
	set_surplus(x,1)
	
    elif get_priority_value(x) == 2.0:	# IF PRODUCTION LEAF
      if mp_surp_flag:
	log.info("Multi-core accept_surplus is True, ensure accept_surplus is turned off.")
	set_surplus(x,0)
      else:
	# if TODO CHECK FOR SPIKE FIRST:
	#if check_for_spike(x):
	  #log.info("Multi-core accept_surplus is False, and spike found for %s in past hour", x)
	if avg < thresh:
	  log.info("Multi-core accept_surplus is False, and past hr. avg. of %s < threshold.", x)
	  set_surplus(x,0)
	else:
	  log.info("Multi-core accept_surplus is False, and past hr. avg. of %s > threshold.", x)
	  set_surplus(x,1)
      

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
  #log.info("!!atlas_group_quotas table surplus changes possible!!")
  #surplus_check()
  #log.info("")
  #log.info("accept_surplus Summary")
  #surplus_summary = ''
  #for x in priority_list:
    #log.info(x + ': ' + str(get_surplus(x)))

  log.info("")
  order_by_priority()
  for x in priority_list:
    flag = check_for_spike(x)
    print 'Spike Flag: ' + str(flag)
    log.info("")
  #name = 'group_atlas.prod.production'
  ##name = 'group_atlas.prod.mp'
  #flag = check_for_spike(name)
  #print 'Production Spike Reduction Flag: ' + str(flag)
  #log.info("")
  
  #name = 'group_atlas.prod.mp'
  ##name = 'group_atlas.prod.mp'
  #flag = check_for_spike(name)
  #print 'Mp Spike Reduction Flag: ' + str(flag)
  #log.info("")
  cur.close()
  con.close()

# To test
if __name__ == '__main__':
  try:
    sys.exit(do_main())
  except Exception:
    log.exception("Uncaught exception")
    sys.exit(1)