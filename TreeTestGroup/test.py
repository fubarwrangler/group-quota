#!/usr/bin/python

# *****************************************************************************
# Script which initializes the group tree, and analyzes the current work group's 
# queue amounts in order to dynamically determine surplus flag modifications.
# This allows the script to automate work load balancing in a timely and reactive  
# way, which should reduce job wait times and minimize group queue amounts, 
# especially for muti-core jobs.
#
# 1. Initialize the root group node
# 2. Create the group tree
# 3. Traverse the tree and analyze weighted leaf surplus requirements Based upon 
#    recent queue amount analysis. Also returns a list of leaf parental nodes.
# 4. Using the returned parental list, compare each parent's children in order 
#    to adjust accept_surplus flags based upon prioritized sibling availability 
#    and needs.
# 5. Once the surplus values are finalized, update the data table with the 
#    new values, if changed
#
# By: Mark Jensen -- mvjensen@rcf.rhic.bnl.gov -- 7/8/14
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

logfile = "/home/mvjensen/dynamicgroups/TreeTestGroup/surplusLog.log"

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
  
# Populates the priority_list with the names of the tree leaves for debugging
def order_by_priority():
  # OBTAIN LIST OF GROUPS WITH PRIORITY > 0
  cur.execute(get_Mysql_sorted_priority_list % (group_name, dbtable, priority, priority))
  results = [i[0] for i in cur.fetchall()]
  for x in results:
    priority_list.append(x)

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
  
  #amounts = [5,40,0,180,14,178,88,188,0,166,999,160]		# For Debug
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
	      
	      # Only check first 8 for surplus
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
    log.info("Switching on accept surplus for %s", name)

  return spike_flag

def surplus_check(group):
    avg = get_average_hour_queue(group.name)
    log.info("")
    log.info("Name: %s, Past hour Avg: %f, Thresh: %d", group.name, avg, group.threshold)
    
    # Reduce work to do by recognizing no queue
    if avg == 0: 
      log.info("Average is 0, set accept_surplus to 0, if possible and skip processing.")
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

def get_surplus_parents(self):
  parents = set()
  def child_search(node):
    if node is not None:
      if not node.children and node.priority > 0:
	surplus_check(node)
	parents.add(node.parent)
      for n in node.children.values():
	child_search(n)
  child_search(self)
  return parents

def compare_surplus(parent):
  
  log.info("")
  log.info("Comparing Surplus For Children of Parent %s", parent.name)
  # Initialize flags for parent's children by core
  eight_core_flag = False
  dual_core_flag = False
  single_core_flag = False
  
  # Set flag values based on needed surplus
  for x in parent.children.values():
    if x.priority == 8.0:
      if x.accept_surplus == 1:
	eight_core_flag = True
    elif x.priority == 2.0:
      if x.accept_surplus == 1:
	dual_core_flag = True
    else:
      if x.accept_surplus == 1:
	single_core_flag = True

  log.info("Surplus flags set as:")
  log.info("8-core: %s, 2-core: %s, 1-core: %s", eight_core_flag, dual_core_flag, single_core_flag)
  # Adjust accept_surplus based on sibling needs
  for x in parent.children.values():
    if x.priority == 8.0: #Check 8 Core Comparisons
      if not dual_core_flag or not single_core_flag:
	if x.accept_surplus == 1:
	  log.info("Surplus allowed for 8 core group: %s, and set to 1", x.name)
	else:
	  log.info("Surplus allowed for 8 core group: %s, but not needed", x.name)
      else:
	log.info("Surplus for %s not allowed", x.name)
	x.accept_surplus = 0
	
	
    elif x.priority == 2.0: #Check 2 Core Comparisons
      if not eight_core_flag or not single_core_flag:
	if x.accept_surplus == 1:
	  log.info("Surplus allowed for dual core group: %s, and set to 1", x.name)
	else:
	  log.info("Surplus allowed for dual core group: %s, but not needed", x.name)
      else:
	log.info("Surplus for %s not allowed", x.name)
	x.accept_surplus = 0
	
    else:
      if not eight_core_flag and not dual_core_flag: #Check Single Core Comparisons
	if x.accept_surplus == 1:
	  log.info("Surplus allowed for single core group: %s, and set to 1", x.name)
	else:
	  log.info("Surplus allowed for single core group: %s, but not needed", x.name)
      else:
	log.info("Surplus for %s not allowed", x.name)
	x.accept_surplus = 0
  return

# TODO make sure Analysis Parent is set to 0 surplus
  

# To test
if __name__ == '__main__':
  
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
    
  # Find and return the parents of the priority leaves
  # Also sets the temporary accept_surplus for each leaf based on current data
  parents = get_surplus_parents(tree)
  
  # Adjusts the accept_surplus for each leaf based upon sibling comparisons
  for p in parents:
    compare_surplus(p)
  log.info("")
  
  ################## FOR DEBUG ##################
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
