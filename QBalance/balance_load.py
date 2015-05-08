#!/usr/bin/python

import logging

from group.db import build_groups_db
import demand.idlejobs


from log import setup_logging

log = setup_logging('foo', backup=1, size_mb=20, level=logging.INFO)
groups = build_groups_db()


def get_candidate_for_surplus(root):
    candidates = sorted(root.get_children(), key=lambda x: -x.weight)
    for idx, group in enumerate(candidates):
        # print candidates[:idx]
        if group.demand == 0:
            break


demand.idlejobs.populate(groups)

get_candidate_for_surplus(groups['group_atlas']['prod'])

groups.print_tree()
