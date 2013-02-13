#!/usr/bin/python

from common import *

# Depending on 'auth', show edit fields for quota or all values
def edit_quotas(data, total, auth):

    print '<h2>Edit Group Quotas</h2><hr>'
    print '<p style="color: blue">Quotas should sum to %d</p>' % total

    if auth == AUTH_FULL:
        print '<p style="padding-right: 40%; color: red">Warning: As an authorized user, you can '
        print 'change the quota sum, so be sure to check your numbers.</p>'

    tab = HTMLTable('class="edit"')
    print '<form enctype="multipart/form-data" method=POST action="%s">' % SCRIPT_NAME
    if auth == AUTH_FULL:
        for i in ('Group Name', 'Quota (orig) (real)', 'Priority (orig)', 'Accept Surplus &nbsp;&nbsp;(orig)'):
            tab.add_hr(i, 'caption="%s"' % i)
    else:
        for i in ('Group Name', 'Quota', 'Priority', 'Accept Surplus'):
            tab.add_hr(i, 'caption="%s"' % i)
    alt = 0

    children = get_children_quota_sum(data)
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
        myquota = row[1] - children[row[0]]
        tab.add_td('%s (%d) (%d)' % ('<input type="text" value="%d" size="6" name="%s_quota">' % (myquota, row[0]), myquota, row[1]))
        if auth == AUTH_FULL:
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
def check_quota_changes(data, formdata, total, auth):

    print '<h2>Updating Group Quotas</h2><hr>'
    new_total = 0

    children = get_children_quota_sum(data)
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
        if auth != AUTH_FULL:
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

    children = get_children_quota_sum(data)
    adjustments = {}
    n_updates = 0
    for grp_name, old_quota, old_prio, old_regroup, busy in data:

        new_quota = int(formdata.getfirst(grp_name + '_quota', '')) + children[grp_name]
        new_prio = float(formdata.getfirst(grp_name + '_prio', '1.0'))
        new_regroup = bool(int(formdata.getfirst(grp_name + '_regroup', 0)))

        quota_diff = new_quota - old_quota

        parents = get_parents(data, grp_name)

        if new_quota != old_quota:
            updates.append('UPDATE %s SET quota = %d WHERE group_name = "%s"' % (TABLE, new_quota, grp_name))
            log = "\t'%s' quota changed from %d -> %d\n" % (grp_name, old_quota, new_quota)
            msg += "<li>%s</li>\n" % log.strip()
            for parent_name in (x[0] for x in parents):
                if parent_name in adjustments:
                    adjustments[parent_name] += quota_diff
                else:
                    adjustments[parent_name] = quota_diff
                logmsg = "\t(parent update) '%s' quota adjusted by %d\n" % (parent_name, quota_diff)
                msg += "<ul><i>%s</i></ul>\n" % logmsg.strip()
                log += logmsg

            logstr += log
            n_updates += 1

        if new_prio != old_prio:
            updates.append('UPDATE %s SET priority = %f WHERE group_name = "%s"' % (TABLE, new_prio, grp_name))
            log = "\t'%s' priority changed from %f -> %f\n" % (grp_name, old_prio, new_prio)
            msg += "<li>%s</li>\n" % log.strip()
            logstr += log
            n_updates += 1

        if new_regroup != old_regroup:
            updates.append('UPDATE %s SET accept_surplus = %d WHERE group_name = "%s"' % (TABLE, new_regroup, grp_name))
            if new_regroup:
                regroup_str = "True"
            else:
                regroup_str = "False"
            log = "\t'%s' accept_surplus changed to %s\n" % (grp_name, regroup_str)
            msg += "<li>%s</li>\n" % log.strip()
            logstr += log
            n_updates += 1
    msg += "</ul>\n"

    if len(updates) == 0:
        print '0 fields changed, not updating database<hr>'
        print '<br><a href="./%s">Go Back</a>' % SCRIPT_NAME
    else:
        print '%d fields changing, updating<br>' % len(updates)
        print msg
        for name in adjustments:
            if adjustments[name]:
                qry = 'UPDATE %s SET quota = quota + %d ' % (TABLE, adjustments[name]) + \
                      'WHERE group_name = "%s"' % name
                updates.append(qry)

        db_execute(updates, user=db_config["update_user"], p=db_config["update_pass"])
        #print "<br>".join(updates)
        log_action('User %s changed %d fields\n%s' % (webdocs_user, n_updates, logstr))

        print '<br>Database updated successfully<hr>'
        print '<br><a href="./%s">Go Back</a> and refresh the page to see new values' % SCRIPT_NAME


