#!/usr/bin/python

# *****************************************************************************
# Script which initializes the group tree, and analyzes the current work group's 
# queue amounts in order to dynamically determine surplus flag modifications.
# This allows the script to automate work load balancing in a timely and reactive  
# way, which should limit idle CPUs, reduce job wait times and minimize group 
# queue amounts, especially for muti-core jobs.
#
#           #### Code heavily commented and logged throughout. ####
#
# 1. Initialize the root group node
# 2. Create the group tree
# 3. Set the accept_surplus value for group_grid. (Currently always set to 1)
# 4. First pass. Traverse the tree using DFS. As the function traverses, it
#    calculates the queue amounts for jobs waiting to be done. This is done in
#    a bottom up way such that Parents' queues will always be the sum of their children. 
# 5. Second Pass. Traverse the tree using DFS. This time calculate the accept_surplus 
#    flags based upon the amount in the queue, as well as the demand of any siblings
#    Ensures that the surplus is set in a priority based context. 
#    i.e. -- Multi-core before single core.
# 6. Once the surplus values are finalized, update the data table with the 
#    new values, if changed#
#
# Simplified Order:
#	1. Create tree
#	2. Set group_grid surplus
#	3. First pass: Determine the queue amounts for each node
#	4. Second pass. Determine the surplus flags based upon demand and priority
#	5. Set new flag values, if possible(no flag flapping)
#
#
# By: Mark Jensen -- mvjensen@rcf.rhic.bnl.gov -- 7/22/14
#
# *****************************************************************************

import sys
import MySQLdb
import logging
import datetime
from group import Group

############################ VARIABLES ############################
# List of leaf group names sorted by priority for debugging
group_list = []

# Spike multiplier used to multiply threshold and determine if queue spike is present
spike_multiplier = 2

# Rapid reduction modifier, to determine if the amount has decreased the necessary percentage
reduce_mod = .875 # Checks if the spike has dropped by 1/4

logfile = "/home/mvjensen/dynamicgroups/TreeTestGroup/atlasSurplus.log"

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
get_Mysql_priority_list = 'SELECT %s FROM %s;'

logging.basicConfig(format="%(asctime)-15s (%(levelname)s) %(message)s",
                    filename=None if '-d' in sys.argv else logfile,
                    level=logging.DEBUG if '-d' in sys.argv else logging.INFO)

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
# Populates the group_list with the names of the tree leaves for debugging		 #
def get_group_list():								 	 #
  # OBTAIN LIST OF GROUPS WITH PRIORITY > 0						 #
  cur.execute(get_Mysql_priority_list % (group_name, dbtable))				 #
  results = [i[0] for i in cur.fetchall()]						 #
  for x in results:									 #
    group_list.append(x)								 #
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
  
  amounts = get_past_hour_queue_amounts(group.name)
  spike_flag = False			# Initialize to False
  surplus_flag = False
  length = len(amounts)
  
  #Prevents group_grid from being checked
  if length == 0:
    return True
  
  group.queue = amounts[length-1]
  
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
    
    log.info("Name: %s, Past hour Avg: %s, Thresh: %d", group.name, str(avg), group.threshold)
      
    # Spike surplus evaluations handled in method
    if check_for_spike(group, avg, group.threshold):
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
  greater_priority_list = (x for x in siblings if x.priority>group.priority)
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
      for x in parent.children.values():
	if x.children:	# If the node has children, all set to 0
	  log.info("#NO AVAILABLE RESOURCES, ALL SET TO 0.[DONE]")
	  for x in parent.children.values():
	    x.accept_surplus = 0
	  break
	else:
	  # if the node is a leaf node, priority takes precedence
	  log.info("#NO AVAILABLE RESOURCES, HIGHEST GETS PRIORITY.[DONE]")
	  priority_list = (x for x in parent.children.values() if x.priority<group.priority)
	  for x in priority_list:
	    x.accept_surplus = 0
	  break
      break
      
  log.info("#")
  log.info("### Post-Compare Values ###")
  for x in parent.children.values():
    log.info("#Name: " + x.name + ", accept_surplus: " + str(x.accept_surplus))
  log.info("##############################")
  log.info("")
  return

# Sums the children's queue amounts to set the parent's queue amount
def calcParentQueues(parent):
  child_queue_sum = 0
  for group in parent.children.values():
    child_queue_sum = child_queue_sum + group.queue
  parent.queue = child_queue_sum
  return

# DFS which sets the childrens queue amounts, and then sum for their parents
def calculateQueues(root):
  def visit_recursion(node, visited):
    children = node.children.values()
    visited.append(node)
    for node in children:
      if node not in visited:
	visit_recursion(node, visited)
	if node.children:
	  # if backtracking and node has children, sum them
	  calcParentQueues(node)
	# else if leaf node, set the surplus accordingly
	elif not node.children and node.priority > 0:
	  group_surplus_check(node)
  # Begin search with empty visited list
  visit_recursion(root, [])
  
  
# Used to set the parental surplus flag based upon sibling demand 
def parent_surplus_check(parent):
  log.info("#Group: %s, queue sum: %d", parent.name, parent.queue)
  if parent.queue == 0:
    parent.accept_surplus = 0
    log.info("#Group: %s, Sum of children's queues = 0, set surplus to 0", parent.name)
  else:
    sibling_list = (x for x in parent.parent.children.values() if x.name!=parent.name)
    for x in sibling_list:
      if x.queue > 0:
	log.info("#Group: %s, Demand found in sibling, set surplus to 0", parent.name)
	parent.accept_surplus = 0
	return
    log.info("#Group: %s, Siblings allow demand, set surplus to 1", parent.name)
    parent.accept_surplus = 1
    return

# Comparison traversal, from the bottom up
def comparison_traversal(root):
  def visit_recursion(node, visited):
    children = node.children.values()
    visited.append(node)
    for node in children:
      if node not in visited:
	visit_recursion(node, visited)
	if node.children:
	  # if backtracking and node has children, compare them
	  parent_surplus_check(node)
	  compare_children_surplus(node)
  # Begin search with empty visited list
  visit_recursion(root, [])
  # final compare of root's children -- currently atlas and grid
  compare_children_surplus(root)
  
# Initialize group_grid accept_surplus flag to '1'
def set_group_grid(root):
  group = root.get_by_name('group_grid')
  group.accept_surplus = 1
                

def do_main():
  
  log.info("############################## SURPLUS QUERY ##############################")

  # Set root
  root = Group('<root>') 
  
  # Step 1.
  # Create Group Tree Structure from Table
  tree = root.tree_creation(cur, con)
  
  # Step 2.
  # Initialize group_grid accept_surplus flag to '1'
  set_group_grid(root)
    
  ############## FOR DEBUG ##############
  get_group_list()			#
  group_list.sort()
  for x in group_list:			#
    avg = get_average_hour_queue(x)	#
    log.info(x + ' AVG.: ' + str(avg))	#
  #######################################
  
  # Step 3.
  # Calulate each node's queue amount
  calculateQueues(tree)
  
  log.info("")
  
  # Step 4.
  # DFS to visit each node, setting surplus values based upon
  # priority and demand
  comparison_traversal(tree)  
  
  ################## FOR DEBUG ##################
  log.info("Demand:")				#
  for x in group_list:				#
    group = root.get_by_name(x)			#
    log.info(x + ': ' + str(group.queue))	#
  ###############################################
  
  # Step 5.
  # Updates all the values currently in the leaves to the table
  tree.enable_surplus_changes(cur, con) 
  
  
  ################## FOR DEBUG ##################
  log.info("")  				#
  log.info("Surplus After Check")		#
  for x in group_list:				#
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