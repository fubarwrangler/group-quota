#!/usr/bin/python

import os
import sys
import time
import MySQLdb

from cfg import *

webdocs_user = os.environ.get('HTTP_X_MYREMOTE_USER')
#webdocs_user = "willsk"

AUTH_NONE = 0
AUTH_EDIT = 1
AUTH_FULL = 2

SCRIPT_NAME = os.environ['SCRIPT_NAME']

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


def db_execute(command, user="db_query", p=""):

    try:
        conn = MySQLdb.connect(db=db_config["database"], host=db_config["host"], user=user, passwd=p)
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
            conn.rollback()
            sys.exit(1)
        except TypeError:
            print 'Invalid command type, nothing sent to db sent to db'
            sys.exit(1)
        else:
            conn.commit()
        db_data = dbc.fetchall()
    finally:
        dbc.close()
        conn.close()

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


def err_page(title, reason):
    print '<h4><span style="color: red;">ERROR:</span>' + title + "</h4>"
    print '<p>' + reason + '</p>'
    print ' <br> <a href="javascript:window.history.go(-1)">Back</a>'


def get_children_quota_sum(data):
    # Maps name --> sum(quotas of all children one level down)
    child_quotas = {}
    tree_groups = sorted([x[0].split(".") for x in data])

    for grp in tree_groups:
        children = [x for x in tree_groups if x[:len(grp)] == grp and len(x) == len(grp) + 1]
        child_sum = 0
        for child in (".".join(y) for y in children):
            quotas = [x[1] for x in data if x[0] == child][0]
            child_sum += quotas
        child_quotas[".".join(grp)] = child_sum

    return child_quotas


def get_top_level_groups(data):
    return [row for row in data if row[0].count(".") == 0]


def get_parents(data, name):
    arr = name.split(".")[:-1]
    parents = list()
    while arr:
        parents.append([x for x in data if x[0] == ".".join(arr)][0])
        arr.pop()
    return parents


def get_all_children(data, name):
    me = name.split(".")
    return [x for x in data if x[0].split(".")[:len(me)] == me and len(x[0].split(".")) > len(me)]
