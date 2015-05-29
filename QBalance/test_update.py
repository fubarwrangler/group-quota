#!/usr/bin/python

import logging

import group.file
import group.db

from log import setup_logging

log = setup_logging(None, backup=3, size_mb=40, level=logging.DEBUG)

fg = group.file.build_quota_groups_file('/tmp/atlas-group-definitions')
dg = group.db.build_quota_groups_db()
