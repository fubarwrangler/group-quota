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

import os
import re
import sys
import cgi
import time
import cgitb
import MySQLdb

FARM_USERS = ['awchan', 'hollowec', 'willsk']
AUTHORIZED_USERS = ['jhover', 'mernst', 'Xwillsk', 'hito']


SCRIPT_NAME = 'group_quota.py'
logfile = '/tmp/atlas_groupquota.log'
auth = 0

cgitb.enable()
#webdocs_user = os.environ.get('HTTP_X_MYREMOTE_USER')
webdocs_user = "willsk"



class HTMLTable(object):
    """ A simple HTML table class that lets you index/modify cells """

    def __init__(self, alt):
        self.tab_rows = 0
        self.tab_cols = 0
        self.alt = alt
        self.table = []
        self.header = []
        self.header_alt = []

    def add_td(self, text, alt=''):
        self.table[-1]['data'].append({'text': text, 'alt': alt})

    def add_tr(self, alt=''):
        self.table.append({'data': [], 'alt': alt})

    def add_hr(self, text, alt=''):
        self.header.append(text)
        self.header_alt.append(alt)

    def col_xform(self, idx, func):
        for row in self.table:
            row['data'][idx]["text"] = func(row['data'][idx]["text"])

    def __str__(self):
        out = '<table %s>\n' % self.alt

        if self.header != []:
            out += '  <tr>'
            for h in range(len(self.header)):
                out += ' <th %s>%s</th>' % (self.header_alt[h], self.header[h])
            out += ' </tr>\n'
        for r in self.table:
            out += '  <tr %s>' % r['alt']
            for c in r['data']:
                out += ' <td %s> %s </td>' % (c['alt'], c['text'])
            out += ' </tr>\n'
        return out + '</table>'

    def __getitem__(self, key):
        return self.table[key]


def db_execute(command, database="linux_farm", host="localhost", user="db_query", p=""):

    try:
        conn = MySQLdb.connect(db=database, host=host, user=user, passwd=p)
        dbc = conn.cursor()
    except MySQLdb.Error, e:
        print "DB Error %d: %s" % (e.args[0], e.args[1])
        print '<p><a href="javascript:window.history.go(-1)">Back</a>'
        sys.exit(1)
    try:
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
            print '<p><a href="javascript:window.history.go(-1)">Back</a>'
            sys.exit(1)
        except TypeError:
            print 'Invalid command type, nothing sent to db sent to db'
            sys.exit(1)
        db_data = dbc.fetchall()
    finally:
        dbc.close()

    conn.commit()

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


def main_page(data, total, user):

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
    for i in ('Group Name', 'Quota', 'Priority', 'Accept Surplus', 'Busy*'):
        tab.add_hr(i, 'caption="%s"' % i)
    for row in data:
        tab.add_tr()
        for obj in row:
            tab.add_td(obj, 'class="body"')
    tab.col_xform(3, lambda x: bool(x))

    print page_head

    if auth == 0:
        print '<p>User <i style="color: blue">%s</i> is not authorized to make changes</p>' % user
    if auth == 1:
        print '<p>Warning: User <i style="color: orangered">%s</i> is authorized to change quotas</p>' % user
    if auth == 2:
        print '<p style="color: red">Caution: User <i>%s</i> is authorized to add/remove groups!</p>' % user

    print page_info
    print tab
    print '<p style="font-size: small">*Busy slot info updated every 5 minutes'
    print '<br>*Last updated: %s</p>' % get_last_update()
    print '<p>Total Slots=%d' % total
    print '<form enctype="multipart/form-data" method=POST action="%s">' % SCRIPT_NAME
    if auth != 0:
        print '<input type=submit name="edit" value="Edit Group Quotas" '
        print 'style="float: left; margin-right: 10px">'
        if auth == 2:
            print '<input type="submit" name="alter_groups" value="Add/Remove Groups"><br>'
        else:
            print '<br>'
        print '<br>'

    print '</form>'
    print '<a href="https://webdocs.racf.bnl.gov/Facility/LinuxFarm/%s" style="font-size: small">' % logfile.split('/')[-1]
    print 'Change History</a>'
    print '<br><br><a href="https://webdocs.racf.bnl.gov/docs/service/condor/atlas-group-quota-editor"\
    title="Documentation" target="__blank">Webdocs Documentation</a>'
    print '<br><p style="font-size: small">Page last refreshed %s</p>' % time.ctime()


def get_last_update():
    d = db_execute("SELECT last_update FROM atlas_group_quotas LIMIT 1")
    return d[0][0].strftime("%b %d %I:%M:%S %p")

# Depending on 'auth', show edit fields for quota or all values
def edit_quotas(data, total):

    # TODO: Javascript box that displays current total at all times?
    total = 0
    total += sum(int(x[1]) for x in data)

    print '<h2>Edit Group Quotas</h2><hr>'
    print '<p style="color: blue">Quotas should sum to %d</p>' % total

    if auth == 2:
        print '<p style="padding-right: 40%; color: red">Warning: As an authorized user, you can '
        print 'change the quota sum, so be sure to check your numbers.</p>'

    tab = HTMLTable('class="edit"')
    print '<form enctype="multipart/form-data" method=POST action="%s">' % SCRIPT_NAME
    if auth == 2:
        for i in ('Group Name', 'Quota (orig)', 'Priority (orig)', 'Accept Surplus &nbsp;&nbsp;(orig)'):
            tab.add_hr(i, 'caption="%s"' % i)
    else:
        for i in ('Group Name', 'Quota', 'Priority', 'Accept Surplus'):
            tab.add_hr(i, 'caption="%s"' % i)
    alt = 0
    for row in data:
        checked = ['', '']
        if bool(row[3]):
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
        else:
            tab.add_td('%s %s' % ('<input type="hidden" value="%s" size="4" name="%s_prio">' % (row[2], row[0]), row[2]))
        tf = 'True:<input type="radio" %s value="1" name="%s_regroup">  ' % (checked[0], row[0])
        tf += ' False:<input type="radio" value="0" %s name="%s_regroup">' % (checked[1], row[0])
        tab.add_td('%s &nbsp;&nbsp; (%s)' % (tf, bool(row[3])))
    print tab
    print '<br><h3>*WARNING*</h3> This will update the database and is written to condor every 10 minutes<br>'
    print '<br><input type="submit" name="change_data" value="Upload Changes"> </form>'
    print '<br><a href="./%s">Back</a></html>' % SCRIPT_NAME


# data is from database, formdata is the cgi input, and total is the number the quotas must add up to
def check_quota_changes(data, formdata, total):

    new_total = 0
    # grp_name contains the titles of the queues in the rows of the database
    # formdata.getfirst(grp_name+"") is the user's new data
    for grp_name in (x[0] for x in data):
        quota = formdata.getfirst(grp_name + '_quota', '')
        prio = formdata.getfirst(grp_name + '_prio', '')
        # sanatize the input
        try:
            new_total += int(quota)
        except ValueError:
            err_page('"%s" is not a valid quota' % quota,
                     "Quota must be an integer")
            return False
        try:
            if float(prio) - 1.0 < 0:
                raise ValueError
        except ValueError:
            err_page('"%s" is not a valid priority' % prio,
                     "Priority must be a floating point number >= 1.0")
            return False

    # Check if the user's math is right
    if new_total != total:
        if auth != 2:
            print '<b style="color: red">ERROR:</b> The new quotas sum up to %d, needs to be %d' % (new_total, total)
            print '<br><br><a href="javascript:window.history.go(-1)">Back</a></html>'
            return False
        else:
            print '<b style="color: red">WARNING:</b> The new quotas sum up to %d, previous sum was %d' % (new_total, total)
            print '<br><br>'

    # If we are here the input should all be sanitized and sanity-checked, so we return ok
    return True


# Generate query and update database if values have changed, writing changes to logfile
def apply_quota_changes(data, formdata):
    updates = []
    logstr = ""
    msg = "<ul>\n"

    for grp_name, old_quota, old_prio, old_regroup, busy in data:
        new_quota = int(formdata.getfirst(grp_name + '_quota', ''))
        new_prio = float(formdata.getfirst(grp_name + '_prio', '1.0'))
        new_regroup = bool(int(formdata.getfirst(grp_name + '_regroup', 0)))
        if new_quota != old_quota:
            updates.append('UPDATE atlas_group_quotas SET quota = %d WHERE group_name = "%s"' % (new_quota, grp_name))
            log = "\t'%s' quota changed from %d -> %d\n" % (grp_name, old_quota, new_quota)
            msg += "<li>%s</li>\n" % log.strip()
            logstr += log

        if new_prio != old_prio:
            updates.append('UPDATE atlas_group_quotas SET priority = %f WHERE group_name = "%s"' % (new_prio, grp_name))
            log = "\t'%s' priority changed from %f -> %f\n" % (grp_name, old_prio, new_prio)
            msg += "<li>%s</li>\n" % log.strip()
            logstr += log

        if new_regroup != old_regroup:
            updates.append('UPDATE atlas_group_quotas SET accept_surplus = %d WHERE group_name = "%s"' % (new_regroup, grp_name))
            if new_regroup:
                regroup_str = "True"
            else:
                regroup_str = "False"
            log = "\t'%s' accept_surplus changed to %s\n" % (grp_name, regroup_str)
            msg += "<li>%s</li>\n" % log.strip()
            logstr += log
    msg += "</ul>\n"

    if len(updates) == 0:
        print '0 fields changed, not updating database<hr>'
        print '<br><a href="./%s">Go Back</a>' % SCRIPT_NAME
    else:
        print '%d fields changed, updating<br>' % len(updates)
        db_execute(updates, user="atlas_update", p="xxx")
        print msg
        log_action('User %s changed %d fields\n%s' % (webdocs_user, len(updates), logstr))

        print '<br>Database updated successfully<hr>'
        print '<br><a href="./%s">Go Back</a> and refresh the page to see new values' % SCRIPT_NAME


def alter_groups(data):

    print '<h2>Edit Database Entries</h2>'
    print '<form enctype="multipart/form-data" method=POST action="%s">' % SCRIPT_NAME
    print 'Password to Add/Remove Groups: <input type="password" name="db_pass" size="16"><br>'
    print '<p><i>Add Group</i><hr>'
    tab2 = HTMLTable('class="add_group" border="1"')
    for i in ('Group Name', 'Quota', 'Priority', 'Accept Surplus'):
        tab2.add_hr(i)
    tab2.add_tr()
    tab2.add_td('<input type="text" name="new_name" size="20">')
    tab2.add_td('<input type="text" name="new_quota" size="6">')
    tab2.add_td('<input type="text" name="new_prio" size="5">')
    tab2.add_td('True: <input type="radio" name="new_regroup" value="1"><br>False:<input checked type="radio" name="new_regroup" value="0">')

    print tab2
    print '<br><input type="submit" name="add_group" value="Add New Group">'
    print '<p><i>Remove Groups</i></p><hr>'
    tab = HTMLTable('class="main" border=1')
    for i in ('Group Name', 'Quota', 'Priority', 'Accept Surplus', 'Busy', 'Remove?'):
        tab.add_hr(i, 'caption="%s"' % i)
    for row in data:
        tab.add_tr()
        for obj in row:
            tab.add_td(obj, 'class="body" align="right"')
        tab.add_td('<input type="checkbox" name="groups_to_remove" value="%s">' % row[0])
    tab.col_xform(3, lambda x: bool(x))
    print tab, '<br>'

    print '<input type="submit" name="remove_groups" value="Remove Selected Groups"><br><br>'
    print '<hr><a href="./%s">Back</a>' % SCRIPT_NAME
    print '</form><br><br><h3>*WARNING* Changes to this page will take effect in condor within 10 min!</h3>'


def err_page(title, reason):
    print '<h4><span style="color: red;">ERROR:</span>' + title + "</h4>"
    print '<p>' + reason + '</p>'
    print ' <br> <a href="javascript:window.history.go(-1)">Back</a>'

def add_group(data, formdata):

    print "<h2>Adding groups</h2><hr>"
    name, quota, prio, surplus = (formdata.getfirst('new_name'), formdata.getfirst('new_quota'),
                                  formdata.getfirst('new_prio'), formdata.getfirst('new_regroup'))
    if surplus:
        surplus_str = "True"
    else:
        surplus_str = "False"

    password = formdata.getfirst('db_pass', '')

    if password == '':
        err_page('No Password Entered, please go back and enter one', '')
        return 1

    # Sanitize input -- match heirarchical groups
    if re.match(r"^group_(\w+)(\.\w+)*$", name):
        tree_groups = [x[0].split(".") for x in data]
        hg_list = name.split(".")
        # If a sub-group, check parents exist
        if len(hg_list) > 1 and hg_list[:-1] not in tree_groups:
                parent = "<b>" + ".".join(hg_list[:-1]) + "</b>"
                err_page('"%s" invalid parents' % name, "Parent group %s needs to exist first" % parent)
                return 1
        elif name in [x[0] for x in data]:
            err_page("'%s' already exists" % name, "Group names mus tbe unique")
            return 1
    else:
        err_page('"%s" is not a valid name' % name,
        """Must be formatted like group_XXX where XXX is one or more groups
           of letters, numbers, or underscore separated, if more than one,
           by a period.""")
        return 1

    try:
        int(quota)
    except ValueError:
        err_page('"%s" is not a valid quota' % quota,
                 "Quota must be an integer")
        return 1
    try:
        if float(prio) - 1.0 < 0:
            raise ValueError
    except ValueError:
        err_page('"%s" is not a valid priority' % prio,
                 "Priority must be a floating point number >= 1.0")
        return 1

    query = "INSERT INTO atlas_group_quotas (group_name,quota,priority,accept_surplus)"
    query += " VALUES ('%s', %s, %s, '%s')" % (name, quota, prio, surplus)
    db_execute(query, user="atlas_edit", p=password)
    logstr = "User %s added group '%s'\n" % (webdocs_user, name)
    logstr += "\tquota=%s, priority=%s, surplus=%s\n" % (quota, prio, surplus_str)
    log_action(logstr)
    print 'Added group "<b>%s</b>"' % name
    print '<br><hr><a href="./%s">Go Back</a>' % SCRIPT_NAME


def remove_groups(data, formdata):

    print "<h2>Removing groups</h2><hr>"
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

    conflicts = {}

    tree_groups = [x[0].split(".") for x in data]
    hgq_list = [x.split(".") for x in grouplist]

    # Check you are not removing a parent that has children that aren't marked to be removed too
    for group in hgq_list:
        bad_groups = [x for x in tree_groups if x[:len(group)] == group \
                      and len(x) > len(group) and x not in hgq_list]
        if bad_groups:
            conflicts[".".join(x for x in group)] = bad_groups

    if conflicts:
        print "<span style='color: red; font-weight: bold;'>ERROR:</span> "
        print "The following groups cannot be removed because they have"
        print "dependent groups that are not going to be removed:\n<ul>"
        for g, c in conflicts.items():
            print "<li><b>%s</b> is a parent of:<ol>" % g
            print "<li>%s</li>" % "</li><li>".join([".".join(y) for y in c])
            print "</ol></li>"
        print "</ul>"
        print ' <br> <a href="javascript:window.history.go(-1)">Back</a>'
        return 1

    for group in grouplist:
        commands.append('DELETE FROM atlas_group_quotas WHERE group_name = "%s";' % group)
        logstr += "\tDELETED group '%s'\n" % group

    db_execute(commands, user="atlas_edit", p=password)
    log_action('User %s removed %d groups\n%s' % (webdocs_user, len(commands), logstr))

    print 'Removed the following %d group(s): <br><b><ul><li>%s</ul></b>' % (len(commands), "<li>".join(grouplist))
    print '<br><hr><a href="./%s">Go Back</a>' % SCRIPT_NAME


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
    table.edit tr.alt { background-color: #b0eeb0; }
    span.top p { padding-right:40%; }
  </style>
</head>
<body>
"""


def do_main():
    global auth, webdocs_user, cgi_data

    query = "SELECT group_name,quota,priority,accept_surplus,busy FROM " + \
            "atlas_group_quotas ORDER BY group_name"
    db_data = db_execute(query)

    if webdocs_user:

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
        if 'edit' in cgi_data:
            edit_quotas(db_data, q_total)
        #Process changes from above page
        elif 'change_data' in cgi_data:
            print '<h2>Updating Group Quotas</h2><hr>'
            if check_quota_changes(db_data, cgi_data, q_total):
                apply_quota_changes(db_data, cgi_data)

        # If Add/Remove groups was clicked
        elif 'alter_groups' in cgi_data:
            alter_groups(db_data)
        # Preform actions set in alter_groups page
        elif 'add_group' in cgi_data:
            add_group(db_data, cgi_data)
        elif 'remove_groups' in cgi_data:
            remove_groups(db_data, cgi_data)

        #Default to show home table
        else:
            main_page(db_data, q_total, webdocs_user)
    else:
        print "<p>Error: Undefined user, how did you get here?\n"
        print '</p><hr><a href="javascript:window.history.go(-1)">Back</a></html>'

if __name__ == "__main__":

    print 'Content-type: text/html\n'
    print header

    try:
        do_main()
    finally:
        print "</body>\n</html>"
