#!/usr/bin/python

# Desc: This script provides the web frontend to the database (on database) that holds
#       the Atlas group-quota information in it.  It allows only 'AUTHORIZED_USERS'
#       to change the group quotas, restricting the total to remain constant.
#       Users in 'FARM_USERS' are allowed to change anything in a group, as well
#       as create and delete groups, if they know the password to do so.
#
# By: William Strecker-Kellogg -- willsk@bnl.gov
#
# CHANGELOG:
#   8/10/10     v1.0 to be put into production


# NOTE: This script works in conjuction with condor03:/home/condor/CONFIG/scripts/update_quotas.py
#       and the farmweb01:/var/www/public/cronjobs/update_db_condor_usage.py, which
#       write database changes to the condor config files and update the busy
#       slots in each group respectively.


import cgitb, cgi
import MySQLdb
import os, sys, time, re


FARM_USERS = ['awchan','hollowec','willsk']
AUTHORIZED_USERS = ['jhover','mernst','psalgado','Xwillsk']

SCRIPT_NAME = 'group_quota.py'
logfile = '/var/www/staff/atlas_groupquota.log'


cgitb.enable()


class HTMLTable:
    """ A simple HTML table class that lets you index/modify cells """

    def __init__(self, alt):
        self.tab_rows = 0
        self.tab_cols = 0
        self.alt = alt
        self.table = []
        self.header = []
        self.header_alt = []

    def add_td(self, text, alt=''):
        self.table[-1]['data'].append({'text':text, 'alt':alt})

    def add_tr(self, alt = ''):
        self.table.append({'data':[], 'alt':alt})

    def add_hr(self, text, alt = ''):
        self.header.append(text)
        self.header_alt.append(alt)

    def __str__(self):
        out = '<table %s>\n' % self.alt

        if self.header != []:
            out += '  <tr>'
            for h in range(len(self.header)):
                out += ' <th %s>%s</th>' % (self.header_alt[h],self.header[h])
            out += ' </tr>\n'
        for r in self.table:
            out += '  <tr %s>' % r['alt']
            for c in r['data']:
                out += ' <td %s> %s </td>' % (c['alt'], c['text'])
            out += ' </tr>\n'
        return out + '</table>'

    def __getitem__(self, key):
        return self.table[key]


def db_execute(command, database="linux_farm", host="localhost", user="willsk", p=""):

    try:
        conn = MySQLdb.connect(db=database,host=host,user=user,passwd=p)
        dbc = conn.cursor()
    except MySQLdb.Error, e:
        print "DB Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    try:
        if (type(command) is list or type(command) is tuple) and len(command) > 0:
            for item in command:
                dbc.execute(item)
        elif type(command) is str:
            dbc.execute(command)
        else:
            raise TypeError
    except MySQLdb.Error, e:
        print "DB Error %d: %s" % (e.args[0], e.args[1])
        dbc.close()
        sys.exit(1)
    except TypeError:
        print 'Invalid command type, nothing sent to db sent to db'
        dbc.close()
        sys.exit(1)

    db_data = dbc.fetchall()
    dbc.close()
    return db_data


def log_action(comment):
    try:
        fp = open(logfile, 'a')
    except:
        print 'Cannot open logfile %s' % logfile
        sys.exit(1)

    output = time.ctime() + ': '
    output += comment
    fp.write(output)
    fp.close()



def main_page(data, total, user, auth):

    page_head = '<span class="top"><p><h2>ATLAS Condor Group Quotas:</h2></p><hr />'
    page_info = \
    """<p>With this page, you can edit the number of slots in each group.  The number
    of slots is called that group's "Quota" and determines the maximum amount of
    resources that condor allocates to that group.  As the sum of all the quotas
    must add up to the total number of slots available, this sum cannot change.
    <b>If you reallocate resources from one quota to another, make
    sure that this sum remains constant, or the change will not take effect.</b>
    """

    tab = HTMLTable('class="main" border=1')
    for i in ('Group Name', 'Quota', 'Priority', 'Auto Regroup', 'Busy*'):
        tab.add_hr(i, 'caption="%s"' % i)
    for row in data:
        tab.add_tr()
        for obj in row:
            tab.add_td(obj, 'class="body" align="right"')



    print page_head

    if auth == 0:
        print 'User <i style="color: blue">%s</i> is not authorized to make changes' % user
    if auth == 1:
        print 'User <i style="color: red">%s</i> is authorized to change quotas' % user
    if auth == 2:
        print '<p style="color: red">Caution: User <i>%s</i> is authorized to add/remove groups!</p>' % user

    print page_info
    print tab
    print '<p style="font-size: small">*Busy slot info updated every 5 minutes'
    print '<br>*Last updated: %s</p>' % get_last_update('%b %d %I:%M:%S %p')
    print '<p>Total Slots=%d' % total
    print '<form enctype="multipart/form-data" method=POST action="%s">' % SCRIPT_NAME
    if auth != 0:
        print '<input type=submit name="edit" value="Edit Group Quotas"> <br><br>'
    if auth == 2:
        print '<input type="submit" name="alter_groups" value="Add/Remove Groups"> '

    print '</form> <br>'
    print '<br><a href="https://webdocs.racf.bnl.gov/Facility/LinuxFarm/%s" style="font-size: small">' % logfile.split('/')[-1]
    print 'Change History</a>'
    print '<br><br><a href="https://webdocs.racf.bnl.gov/docs/service/condor/atlas-group-quota-editor"\
    title="Documentation" target="__blank">Webdocs Documentation</a>'
    print '<br><p style="font-size: small">Page last refreshed %s</p>' % time.ctime()

# Depending on 'auth', show edit fields for quota or all values
def edit_quotas(data, total, auth=0):

    # TODO: Javascript box that displays current total at all times?
    total = 0
    for row in data:
        total += int(row[1])


    print '<h3>Edit Group Quotas</h3>'
    print '<p style="color: red">Quotas must sum to %d</p><hr>' % total

    if auth == 2:
        print '<p style="padding-right: 40%; color: red">Warning: As an authorized user, you can '
        print 'change the quota sum, so be sure to check your numbers.</p>'

    tab = HTMLTable('class="edit"')
    print '<form enctype="multipart/form-data" method=POST action="%s">' % SCRIPT_NAME
    if auth == 2:
        for i in ('Group Name','Quota (orig)','Priority (orig)','Auto Regroup &nbsp;&nbsp;(orig)'):
            tab.add_hr(i, 'caption="%s"' % i)
    else:
        for i in ('Group Name','Quota','Priority','Auto Regroup'):
            tab.add_hr(i, 'caption="%s"' % i)
    alt = 0
    for row in data:
        checked = ['','']
        if row[3] == 'TRUE':
            checked[0] = 'checked="checked"'
        else:
            checked[1] = 'checked="checked"'
        if alt:
            tab.add_tr('class="alt"')
        else:
            tab.add_tr()
        alt ^= 1
        tab.add_td(row[0])
        tab.add_td('%s (%s)' % ('<input type="text" value="%d" size="6" name="%s_quota">' % (row[1], row[0]), row[1]))
        if auth == 2:
            tab.add_td('%s (%s)' % ('<input type="text" value="%s" size="4" name="%s_prio">' % (row[2], row[0]), row[2]))
            tf =  'True:<input type="radio" %s value="True" name="%s_regroup">  ' % (checked[0], row[0])
            tf += ' False:<input type="radio" value="False" %s name="%s_regroup">' % (checked[1], row[0])
            tab.add_td('%s &nbsp;&nbsp; (%s)' % (tf, row[3].capitalize()))
        else:
            tab.add_td('%s %s' % ('<input type="hidden" value="%s" size="4" name="%s_prio">' % (row[2], row[0]), row[2]))
            tf =  '<input type="hidden" value="%s" name="%s_regroup"> ' % (row[3], row[0])
            tab.add_td('%s %s' % (tf, row[3].capitalize()))

    print tab
    print '<br><h3>*WARNING*</h3> This will update the database and is written to condor every 10 minutes<br>'
    print '<br><input type="submit" name="change_data" value="Upload Changes"> </form>'
    print '<br><a href="./%s">Back</a></html>' % SCRIPT_NAME

# data is from database, formdata is the cgi input, and total is the number the quotas must add up to
def check_quota_changes(data, formdata, total, auth):

    new_total = 0
    # grp_name contains the titles of the queues in the rows of the database
    # formdata.getfirst(grp_name+"") is the user's new data
    for grp_name in [x[0] for x in data]:
        quota = formdata.getfirst(grp_name+'_quota', '')
        prio = formdata.getfirst(grp_name+'_prio', '')
        regroup = formdata.getfirst(grp_name+'_regroup', '')
        # sanatize the input
        if not re.match('^\d+$', quota):
            print '<b>ERROR:</b> Please enter a valid whole number in the quota box!'
            print '<br><a href="javascript:window.history.go(-1)">Back</a></html>'
            return 0
        if not re.match('(^\d+\.\d+$)|(^\d+$)', prio):
            print '<b>ERROR:</b> Please enter a valid floating point number in the priority box!'
            print '<br><a href="javascript:window.history.go(-1)">Back</a></html>'
            return 0
        # Pedantic, because it comes only from form radio buttons, but why not check it?
        if not re.match('(^TRUE$)|(^FALSE$)', regroup.upper()):
            print '<b>ERROR:</b> Somehow you managed not to enter True or False in the True/False buttons--how!?'
            print '<br><a href="javascript:window.history.go(-1)">Back</a></html>'
            return 0

        new_total += int(quota)

    # Check if the user's math is right
    if new_total != total:
        if auth != 2:
            print '<b>ERROR:</b> The new quotas sum up to %d, needs to be %d' % (new_total, total)
            print '<br><a href="javascript:window.history.go(-1)">Back</a></html>'
            return 0
        else:
            print '<b>WARNING:</b> The new quotas sum up to %d, previous sum was %d' % (new_total, total)
            print '<br>'

    # If we are here the input should all be sanitized and sanity-checked, so we return ok
    return 1

# Generate query and update database if values have changed, writing changes to logfile
def apply_quota_changes(data, formdata, user):
    updates = []
    logstr = ""

    for grp_name, old_quota, old_prio, old_regroup, busy in data:
        new_quota = int(formdata.getfirst(grp_name+'_quota',''))
        new_prio = float(formdata.getfirst(grp_name+'_prio','1.0'))
        new_regroup = formdata.getfirst(grp_name+'_regroup','FALSE').upper()

        if new_quota != old_quota:
            updates.append('UPDATE atlas_group_quotas SET quota = %d WHERE group_name = "%s";' % (new_quota, grp_name))
            logstr += "\t'%s' quota changed from %d -> %d\n" % (grp_name, old_quota, new_quota)

        if new_prio != old_prio:
            updates.append('UPDATE atlas_group_quotas SET priority = %f WHERE group_name = "%s";' % (new_prio, grp_name))
            logstr += "\t'%s' priority changed from %f -> %f\n" % (grp_name, old_prio, new_prio)

        if new_regroup != old_regroup:
            updates.append('UPDATE atlas_group_quotas SET auto_regroup = "%s" WHERE group_name = "%s";' % (new_regroup, grp_name))
            logstr += "\t'%s' regroup changed to %s\n" % (grp_name, new_regroup)

    if len(updates) == 0:
        print '0 fields changed, not updating database<hr>'
        print '<br><a href="./%s">Go Back</a>' % SCRIPT_NAME
    else:
        print '%d fields changed, updating<br>' % len(updates)
        db_execute(updates, user="condor_update",p="XPASSX")
        log_action('User %s changed %d fields\n%s' % (user, len(updates), logstr))

        print '<br>Database updated successfully<hr>'
        print '<br><a href="./%s">Go Back</a> and refresh the page to see new values' % SCRIPT_NAME


def alter_groups(data):

    print '<h2>Edit Database Entries</h2>'
    print '<form enctype="multipart/form-data" method=POST action="%s">' % SCRIPT_NAME
    print 'Password to Add/Remove Groups: <input type="password" name="db_pass" size="16"><br>'
    print '<p><i>Add Group</i><hr>'
    tab2 = HTMLTable('class="add_group" border="1"')
    for i in ('Group Name','Quota','Priority','Auto Regroup'):
        tab2.add_hr(i)
    tab2.add_tr()
    tab2.add_td('<input type="text" name="new_name" size="20">')
    tab2.add_td('<input type="text" name="new_quota" size="6">')
    tab2.add_td('<input type="text" name="new_prio" size="5">')
    tab2.add_td('True: <input type="radio" name="new_regroup" value="TRUE"><br>False:<input checked type="radio" name="new_regroup" value="FALSE">')

    print tab2
    print '<br><input type="submit" name="add_group" value="Add New Group">'
    print '<p><i>Remove Groups</i></p><hr>'
    tab = HTMLTable('class="main" border=1')
    for i in ('Group Name','Quota','Priority','Auto Regroup', 'Busy', 'Remove?'):
        tab.add_hr(i, 'caption="%s"' % i)
    for row in data:
        tab.add_tr()
        for obj in row:
            tab.add_td(obj, 'class="body" align="right"')
        tab.add_td('<input type="checkbox" name="groups_to_remove" value="%s">' % row[0])
    print tab, '<br>'


    print '<input type="submit" name="remove_groups" value="Remove Selected Groups"><br><br>'
    print '<hr><a href="./%s">Back</a>' % SCRIPT_NAME
    print '</form><br><br><h3>*WARNING* Changes to this page will take effect in condor within 15 min!</h3>'


def add_group(data, formdata, user):

    name, quota, prio, regroup = (formdata.getfirst('new_name'),formdata.getfirst('new_quota'),\
                               formdata.getfirst('new_prio'),formdata.getfirst('new_regroup'))
    password = formdata.getfirst('db_pass', '')
    if password == '':
        print 'No Password Entered, please go back and enter one'
        print ' <hr> <a href="javascript:window.history.go(-1)">Back</a>'
        return 1

    # Sanitize input
    if not re.match('^group_[a-zA-Z_0-9]+$', name):
        print '"%s" is not a valid groupname, letters, numbers, and underscore please' % name
        print ' <br> <a href="javascript:window.history.go(-1)">Back</a>'
        return 1
    if not re.match('^\d+$', quota):
        print '"%s" is not a valid quota, whole numbers only' % quota
        print ' <br> <a href="javascript:window.history.go(-1)">Back</a>'
        return 1
    if not re.match('(^\d+\.\d+$)|(^\d+$)', prio):
        print '"%s" is not a valid priority, floating point numbers please' % prio
        print ' <br> <a href="javascript:window.history.go(-1)">Back</a>'
        return 1

    if name in [x[0] for x in data]:
        print '<b>ERROR:</b> cannot have a group with the same name as another group'
        print ' <br> <a href="javascript:window.history.go(-1)">Back</a>'
        return 1

    query =  "INSERT INTO atlas_group_quotas (group_name,quota,priority,auto_regroup)"
    query += " VALUES ('%s', %s, %s, '%s')" % (name, quota, prio, regroup)
    db_execute(query, user="condor_edit", p=password)
    logstr = "User %s added group '%s'\n" % (user, name)
    logstr += "\tquota=%s, priority=%s, auto_regroup=%s\n" % (quota, prio, regroup)
    log_action(logstr)
    print 'Added group "<b>%s</b>"' % name
    print '<br><hr><a href="./%s">Go Back</a>' % SCRIPT_NAME

def remove_groups(data, formdata, user):

    commands = []
    grouplist = formdata.getlist('groups_to_remove')
    password = formdata.getfirst('db_pass', '')

    if password == '':
        print 'No Password Entered, please go back and enter one'
        print ' <hr> <a href="javascript:window.history.go(-1)">Back</a>'
        return 1

    logstr = ""
    if len(grouplist) == 0:
        print 'No Groups Selected, nothing changed'
        print ' <hr> <a href="javascript:window.history.go(-1)">Back</a>'
        return 1
    for group in grouplist:
        commands.append('DELETE FROM atlas_group_quotas WHERE group_name = "%s";' % group)
        logstr += "\tDELETED group '%s'\n" % group

    db_execute(commands, user="condor_edit", p=password)
    log_action('User %s removed %d groups\n%s' % (user, len(commands),logstr))

    print 'Removed the following %d group(s): <br><b><ul><li>%s</ul></b>' % (len(commands), "<li>".join(grouplist))
    print '<br><hr><a href="./%s">Go Back</a>' % SCRIPT_NAME

def get_last_update(fmt):
    last_update = db_execute("SELECT last_change FROM atlas_group_quotas")[0][0]
    return time.strftime(fmt, time.localtime(last_update))





cgi_data = cgi.FieldStorage()

header = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta http-equiv="cache-control" content="no-cache" />
  <meta http-equiv="refresh" content="150">
  <title>ATLAS Group Quotas</title>
  <style type="text/css">
    body { background-color: #9cdede; }
    table.main { empty-cells: show; border-spacing:2px 1px; border-style: outset; }
    table.main th { background-color: #39e354; padding: 5px 10px;}
    table.main td { text-align: left; padding: 2px 4px; }
    table.add_group th { background-color: #39e354; padding: 2px 2px; }
    table.edit { empty-cells: show; border-spacing:5px 2px; }
    table.edit th { text-align: left; background-color: #39e354;}
/*    table.edit td { border-bottom: 2px solid #aa22ff; } */
    table.edit tr.alt { background-color: #b0eeb0; }
    span.top p { padding-right:40%; }
  </style>
</head>
<body>
"""

# ================== Main program statements =======================
print 'Content-type: text/html\n'
print header

webdocs_user = os.environ.get('HTTP_X_MYREMOTE_USER')
query = "SELECT group_name,quota,priority,auto_regroup,busy FROM atlas_group_quotas ORDER BY group_name"
db_data = db_execute(query)

if webdocs_user != None:


    if webdocs_user in AUTHORIZED_USERS:
        auth = 1
    elif webdocs_user in FARM_USERS:
        auth = 2
    else:
        auth = 0

    # need a running total of the quota sum
    q_total = 0
    for row in db_data:
        q_total += int(row[1])

    # If Edit Group Quotas was clicked
    if cgi_data.has_key('edit'):
        edit_quotas(db_data, q_total, auth)
    #Process changes from above page
    elif cgi_data.has_key('change_data'):
        OK = check_quota_changes(db_data, cgi_data, q_total,auth)
        if OK == 0:
            pass
        else:
            apply_quota_changes(db_data, cgi_data, webdocs_user)

    # If Add/Remove groups was clicked
    elif cgi_data.has_key('alter_groups'):
        alter_groups(db_data)
    # Preform actions set in alter_groups page
    elif cgi_data.has_key('add_group'):
        add_group(db_data, cgi_data, webdocs_user)
    elif cgi_data.has_key('remove_groups'):
        remove_groups(db_data, cgi_data, webdocs_user)

    #Default to show home table
    else:
        main_page(db_data, q_total, webdocs_user, auth)
else:
    print "<p>Error: Undefined user, how did you get here?\n"
    print '</p><hr><a href="javascript:window.history.go(-1)">Back</a></html>'


print "</body>\n</html>"

