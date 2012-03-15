#!/usr/bin/python

import os
import re
from common import *

# Show forms with tables to add or remove groups, posts with
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
            err_page("'%s' already exists" % name, "Group names must be unique")
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

