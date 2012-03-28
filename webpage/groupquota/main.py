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

import cgi
import time

from common import *


def main_page(data, total, user, auth):

    page_head = '<span class="top"><p><h2>ATLAS Condor Group Quotas:</h2></p><hr />'
    page_info = \
    """<p>With this page, you can edit the number of slots in each group.  The number
    of slots is called that group's "Quota" and determines the maximum amount of
    resources that condor allocates to that group.  Groups are arranged in a tree,
    with child-groups follwing a dot (.) in the parent's name (a.b -- b is a child
    of a).  The sum of a group's children will be subtracted from the quota here
    ('real' quota includes this), any extra nodes alloted to a non-leaf node will
    apply to that group, i.e. if a = 1 (11 real) and a.b = 10, 1 slot will be
    for jobs with group_a and 10 for jobs with group_a.b
    <p> As the sum of all the quotas must add up to the total number of slots
    available, this sum cannot change.
    <b>If you reallocate resources from one quota to another, make
    sure that this sum remains constant, or the change will not take effect
    unless you are authorized to make those changes.</b>
    """

    def get_last_update():
        d = db_execute("SELECT last_update FROM atlas_group_quotas LIMIT 1")
        return d[0][0].strftime("%b %d %I:%M:%S %p")

    child_quota = get_children_quota_sum(data)

    tab = HTMLTable('class="main" border=1')
    for i in ('Group Name', 'Quota (real)', 'Priority', 'Accept Surplus', 'Busy (sub)*'):
        tab.add_hr(i, 'caption="%s"' % i)
    for row in data:
        tab.add_tr()
        new_row = [x for x in row]
        if child_quota[row[0]] > 0:
            busy_children = sum(int(x[4]) for x in get_all_children(data, row[0]))
            new_row[1] = '%d (%d)' % (row[1] - child_quota[row[0]], row[1])
            new_row[4] = '%d (%d)' % (row[4], busy_children)

        for obj in new_row:
            tab.add_td(obj, 'class="body"')
    tab.col_xform(3, lambda x: bool(x))

    print page_head

    if auth == AUTH_FULL:
        print '<p style="color: red">Caution: User <i>%s</i> is authorized to add/remove groups and change quotas</p>' % user
    elif auth == AUTH_EDIT:
        print '<p>Warning: User <i style="color: orangered">%s</i> is authorized to change quotas</p>' % user
    else:
        print '<p>User <i style="color: blue">%s</i> is not authorized to make changes</p>' % user

    print page_info
    print tab
    print '<p style="font-size: small">*Busy slot info updated every 5 minutes'
    print '<br>*Last updated: %s</p>' % get_last_update()
    print '<p>Total Slots=%d' % total
    print '<form enctype="multipart/form-data" method=POST action="%s">' % SCRIPT_NAME
    if auth != AUTH_NONE:
        print '<input type=submit name="edit" value="Edit Group Quotas" '
        print 'style="float: left; margin-right: 10px">'
        if auth == AUTH_FULL:
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


cgi_data = cgi.FieldStorage()

header = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta http-equiv="cache-control" content="no-cache" />
  <meta http-equiv="refresh" content="180">
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


def render_page():
    global auth, webdocs_user, cgi_data, TABLE

    print 'Content-type: text/html\n'
    print header

    query = "SELECT group_name,quota,priority,accept_surplus,busy FROM " + \
            "%s ORDER BY group_name" % TABLE

    db_data = db_execute(query)
    q_total = sum(x[1] for x in get_top_level_groups(db_data))

    if webdocs_user:

        if webdocs_user in FARM_USERS:
            auth = AUTH_FULL
        elif webdocs_user in AUTHORIZED_USERS:
            auth = AUTH_EDIT
        else:
            auth = AUTH_NONE

        # If Edit Group Quotas was clicked
        if 'edit' in cgi_data:
            import quotaedit
            quotaedit.edit_quotas(db_data, q_total, auth)
        #Process changes from above page
        elif 'change_data' in cgi_data:
            import quotaedit
            if quotaedit.check_quota_changes(db_data, cgi_data, q_total, auth):
                quotaedit.apply_quota_changes(db_data, cgi_data)
        # If Add/Remove groups was clicked
        elif 'alter_groups' in cgi_data:
            import groupedit
            groupedit.alter_groups(db_data)
        # Preform actions set in alter_groups page
        elif 'add_group' in cgi_data:
            import groupedit
            groupedit.add_group(db_data, cgi_data)
        elif 'remove_groups' in cgi_data:
            import groupedit
            groupedit.remove_groups(db_data, cgi_data)

        #Default to show home table
        else:
            main_page(db_data, q_total, webdocs_user, auth)
    else:
        print "<p>Error: Undefined user, how did you get here?\n"
        print '</p><hr><a href="javascript:window.history.go(-1)">Back</a></html>'

    print "</body>\n</html>"
