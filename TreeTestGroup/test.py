#!/usr/bin/python

# *****************************************************************************
# Script which initializes the group tree, and analyzes the current work group's 
# queue amounts in order to dynamically determine surplus flag modifications.
# This allows the script to automate work load balancing in a timely and reactive  
# way, which should limit idle CPUs, reduce job wait times and minimize group 
# queue amounts, especially for muti-core jobs.
#
# 1. Initialize the root group node
# 2. Create the group tree
# 3. Traverse the tree using DFS. As it traverses, the function identifies nodes
#    without children and sets thier surplus flags, if possible(some have a 
#    priority = 0, such as group_atlas.software). If the node has children, it 
#    will determine it's surplus flag based upon the availability 
#    of surplus among its children.
# 4. Once the surplus values are finalized, update the data table with the 
#    new values, if changed#
#
# Simplified Order:
#	1. Create tree
#	2. DFS tree: decide surplus flags based on current need
#	3. Set new flag values, if possible(no flag flapping)
#
#
# By: Mark Jensen -- mvjensen@rcf.rhic.bnl.gov -- 7/18/14
#
# *****************************************************************************

import sys
import MySQLdb
import logging
import datetime
from group import Group

############################ VARIABLES ############################
# List of leaf group names sorted by priority for debugging
priority_list = []

# Spike multiplier used to multiply threshold and determine if queue spike is present
spike_multiplier = 2

# Rapid reduction modifier, to determine if the amount has decreased the necessary percentage
reduce_mod = .875 # Checks if the spike has dropped by 1/4

logfile = "/home/mvjensen/dynamicgroups/TreeTestGroup/surplusCheckLog.log"

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
priority = 'priority'

# MySQL variable getters and setters
get_Mysql_groups = 'SELECT %s FROM %s;'
get_Mysql_Val = 'SELECT %s FROM %s WHERE %s="%s"'
get_Mysql_queue_avg = 'SELECT AVG(%s) FROM %s WHERE TIMESTAMPDIFF(HOUR, %s, NOW()) < 1 AND %s="%s";'
get_Mysql_queue_amounts = 'SELECT %s FROM %s WHERE TIMESTAMPDIFF(HOUR, %s, NOW()) < 1 AND %s="%s";'
get_Mysql_sorted_priority_list = 'SELECT %s FROM %s WHERE %s>0 ORDER BY %s DESC;'

logging.basicConfig(format="%(asctime)-15s (%(levelname)s) %(message)s",
                    filename=None if '-d' in sys.argv else logfile,
                    level=logging.DEBUG if '-d' in sys.argv else logging.INFO)

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
  
##################################### FOR DEBUGGING ######################################
# Populates the priority_list with the names of the tree leaves for debugging		 #
def order_by_priority():								 #
  # OBTAIN LIST OF GROUPS WITH PRIORITY > 0						 #
  cur.execute(get_Mysql_sorted_priority_list % (group_name, dbtable, priority, priority))#
  results = [i[0] for i in cur.fetchall()]						 #
  for x in results:									 #
    priority_list.append(x)								 #
											 #
# Used for info and debugging								 #
def get_surplus(name):									 #
  cur.execute(get_Mysql_Val % (accept_surplus, dbtable, group_name, name))		 #
  value = cur.fetchone()[0]								 #
  return value										 #
##########################################################################################

# Gets the average queue amount for the group over the past hour
def get_average_hour_queue(name):
  cur.execute(get_Mysql_queue_avg % (amount_in_queue, queue_log_table, query_time, group_name, name))
  average = cur.fetchone()[0]
  return average

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
def check_for_spike(group, avg, threshold):
  
  #amounts = [0,0,0,20,0,68,9,0,223,522,800]			# For Debug
  #avg = reduce(lambda x, y: x + y, amounts) / len(amounts) 	# For Debug
  
  amounts = get_past_hour_queue_amounts(group.name)
  spike_flag = False			# Initialize to False
  surplus_flag = False
  length = len(amounts)
  
  
  ## For Debug purposes ##
  log.info("Checking spike for  %s.", group.name)
  log.info("AVERAGE: %d, THRESHOLD: %d * 10 = %d", avg, threshold, threshold*10)
  #########################
  
  if avg < threshold*10: # Queue limit for spike check
    max_index = 0
    max_difference = 0
    limitCheck = threshold*spike_multiplier
    
    test = [x - amounts[i - 1] for i, x in enumerate(amounts)][1:]
    # Index used for testing
    index = test.index(max(test[0:7]))
    
    log.info("MAX DIFFERENCE IN FIRST 8 VALUES: %d, at Amount time: %d", max(test[0:7]), index+1)
    log.info("Spike Threshold = %d",limitCheck)
    
    
    # Check all values for a spike in order to allow a late spike to be checked before reacting to soon
    if max(test) < limitCheck: # if all values are too low, no need to do any extra work
      log.info('NO POSSIBLE SPIKES FOUND')
    else:
      log.info('POSSIBLE SPIKE IN LAST HOUR')
      i = 0
      # Search the entire hour for a Spike, only check sor surplus if spike whithin first 8 values
      while i < length-1:
	diff = amounts[i+1] - amounts[i]
	
	# Update max index and value
	if diff > max_difference:
	  max_index = i+1
	  max_difference = diff
	    
	# Percent increase can only be determined when not starting at zero
	if amounts[i] != 0: 
	  percent = round(float(diff)/float(amounts[i]), 4)
	  percent = percent * 100
	  #log.info("Difference between %d and %d = %d, a  %d  change.", i, i+1, diff, percent)
	  log.info("Difference between %d and %d = %d, a %d%% change.", i, i+1, diff, percent)
	  
	  if percent < 0:
	    log.info('DECREASE DETECTED')
	    
	  elif percent >= 500:
	    if amounts[i+1] >= limitCheck:
	      spike_flag = True
	      
	      # Only check first 8 for surplus flag
	      if i < 7:
		log.info('SPIKE DETECTED, DETERMINING RAPID REDUCTION')
		log.info("Spike = %d, .875 * spike = %d, most recent value = %d", amounts[max_index], amounts[max_index]*reduce_mod, amounts[length-1]) 
		
		if amounts[max_index]*reduce_mod > amounts[length-1]:
		  log.info('SPIKE DECREASING NORMALLY, NO CHANGE NEEDED')
		  surplus_flag = False
		else:
		  log.info('SPIKE NOT DECREASING NORMALLY, SWITCH ON ACCEPT SURPLUS IF POSSIBLE')
		  surplus_flag = True
		  
	    else:
	      log.info('HIGH PERCENTAGE, LOW VALUE. NOT A SPIKE')
	  
	  else:
	    log.info('NOT A SPIKE')
	 
	## STARTING AT ZERO DIFFERENCE MUST BE GREATER THAN SPIKE THRESHOLD
	else: 
	  log.info("Since previous value 0, Difference between %d and %d = %d", i, i+1, diff)
	  if diff > limitCheck:
	    spike_flag = True
	    
	    # Only check first 8 for surplus
	    if i < 7:
	      log.info('SPIKE DETECTED, DETERMINING RAPID REDUCTION')
	      log.info("spike = %d, .875 * spike = %d, most recent value = %d", amounts[max_index], amounts[max_index]*reduce_mod, amounts[length-1]) 
	      if amounts[max_index]*reduce_mod > amounts[length-1]:
		log.info('SPIKE DECREASING NORMALLY, NO CHANGE NEEDED')
		surplus_flag = False
	      else:
		log.info('SPIKE NOT DECREASING NORMALLY, SWITCH ON ACCEPT SURPLUS IF POSSIBLE')
		surplus_flag = True
	  else:
	    log.info('NOT A SPIKE')
	i += 1
	
      log.info("Max diff = %d", max_difference)
      
  else:
    log.info("Queue amount exceeds spike check threshold, spike check unnecessary.")
    
  # if SPIKE NOT DECREASING NORMALLY, SWITCH ON ACCEPT SURPLUS IF POSSIBLE
  if surplus_flag:
    group.accept_surplus = 1
    log.info("Switching on accept surplus for %s", group.name)

  return spike_flag

def group_surplus_check(group):
    avg = get_average_hour_queue(group.name)
    log.info("")
    log.info("Name: %s, Past hour Avg: %f, Thresh: %d", group.name, avg, group.threshold)
    
    # Reduce work to do by recognizing no queue
    if avg == 0: 
      log.info("Average is 0, set accept_surplus to 0, if possible, and skip processing.")
      group.accept_surplus = 0
      
    # Spike surplus evaluations handled in method
    elif check_for_spike(group, avg, group.threshold):
      return
    
    # Below threshold average, little to no load in queue
    elif avg < group.threshold:
      log.info("No spike and avg. below threshold, set accept_surplus to 0, if possible.")
      group.accept_surplus = 0
      
    # Else too much in queue set surplus if possible
    else:
      log.info("No spike but avg. above threshold, set accept_surplus to 1, if possible.")
      group.accept_surplus = 1
    log.info("Name: %s, accept_surplus: %d", group.name, group.accept_surplus) 
    

def lower_priority_surplus_available(group, siblings):
  lesser_priority_list = (x for x in siblings if x.priority<group.priority)
  if sum(1 for _ in lesser_priority_list) == 0:
    log.info("#Its the lowest priority group,")
    return True
  lesser_priority_list = (x for x in siblings if x.priority<group.priority)
  for x in lesser_priority_list:
    if x.accept_surplus == 0:
      if not x.priority == 0: 
	log.info("#Surplus available in lower priority,"),
	return True
  log.info("#Surplus not available in lower priority,")
  return False

def higher_priority_surplus_available(group, siblings):
  greater_priority_list = (x for x in siblings if x.priority>group.priority)
  for x in greater_priority_list:
    if x.accept_surplus == 1:
      log.info("#Surplus flag found in higher priority group,")
      return False
  if sum(1 for _ in greater_priority_list)  == 0:
    log.info("#Its the highest priority group,"),
    return False
  return True

def compare_children_surplus(parent):
  
  log.info("")
  log.info("### Initial Values for %s ###", parent.name)
  for x in parent.children.values():
    log.info("#Name: %s, accept_surplus: %d, priority: %d", x.name, x.accept_surplus, x.priority)
  log.info("#")
  log.info("#Comparing Surplus For Children of Parent %s", parent.name)
  for group in sorted(parent.children.values(), key=lambda x: x.priority, reverse = True):
    log.info("#Checking: " + group.name + ","),
    
    if group.accept_surplus == 0:
      log.info("#Flag remains 0. [DONE]")
      continue
    
    if higher_priority_surplus_available(group, parent.children.values()):
      priority_list = (x for x in parent.children.values() if x.priority<group.priority)
      for x in priority_list:
	x.accept_surplus = 0
      log.info("#Flag remains 1. Setting all lower priority to 0.[DONE]")
      break
    
    elif lower_priority_surplus_available(group, parent.children.values()):
      priority_list = (x for x in parent.children.values() if x.priority<group.priority)
      for x in priority_list:
	x.accept_surplus = 0
      log.info("#Flag remains 1. Setting all lower priority to 0.[DONE]")
      break
    
    else:
      log.info("#NO AVAILABLE RESOURCES, ALL SET TO 0.[DONE]")
      for x in parent.children.values():
	x.accept_surplus = 0
      break
      
  log.info("#")
  log.info("### Post-Compare Values ###")
  for x in parent.children.values():
    log.info("#Name: " + x.name + ", accept_surplus: " + str(x.accept_surplus))
  #log.info("##############################")
  return

def parent_surplus_check(parent):
  for group in parent.children.values():
    if group.accept_surplus == 1:
      log.info("#Group: %s, Surplus flag found in children, set surplus to 1", parent.name)
      parent.accept_surplus = 1
      log.info("##############################")
      return
  parent.accept_surplus = 0
  log.info("#Group: %s, No surplus flag found in children, set surplus to 0", parent.name)
  log.info("##############################")
  return

  
def dfs_traversal(root):
  def visit_recursion(node, visited):
    children = node.children.values()
    visited.append(node)
    for node in children:
      if node not in visited:
	visit_recursion(node, visited)
	if node.children:
	  # if backtracking and node has children, compare them
	  compare_children_surplus(node)
	  parent_surplus_check(node)
	# else if leaf node, set the surplus accordingly
	elif not node.children and node.priority > 0:
	  group_surplus_check(node)
  # Begin search with empty visited list
  visit_recursion(root, [])
  # final compare of root's children -- currently atlas and grid
  compare_children_surplus(root)
                

def do_main():
  
  log.info("############################## SURPLUS QUERY ##############################")

  # Set root
  root = Group('<root>') 
  # Create Group Tree Structure from Table
  tree = root.tree_creation(cur, con)
  
  ############## FOR DEBUG ##############
  order_by_priority()			#
  for x in priority_list:		#
    avg = get_average_hour_queue(x)	#
    log.info(x + ' AVG.: ' + str(avg))	#
  #######################################
  
  # DFS to visit each node setting leaf surplus for priority
  # groups and comparing the children of parents, in a bottom up method
  dfs_traversal(tree)  
  
  ################## FOR DEBUG ##################
  log.info("")
  log.info("Surplus before Check:")		#
  for x in priority_list:			#
    log.info(x + ': ' + str(get_surplus(x)))	#
  ###############################################
  
  # Updates all the values currently in the leaves to the table
  tree.enable_surplus_changes(cur, con) 
  
  ################## FOR DEBUG ##################
  log.info("")  				#
  log.info("Surplus After Check")		#
  for x in priority_list:			#
    log.info(x + ': ' + str(get_surplus(x)))	#
  log.info("")					#
  ###############################################

  cur.close()
  con.close()

if __name__ == '__main__':
  try:
    sys.exit(do_main())
  except Exception:
    log.exception("Uncaught exception")
    sys.exit(1)