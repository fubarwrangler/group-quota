#!/usr/bin/python

from group.db import build_groups_db

root = build_groups_db()
root.print_tree()
