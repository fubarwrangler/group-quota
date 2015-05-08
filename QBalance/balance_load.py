#!/usr/bin/python

from group.db import build_groups_db

groups = build_groups_db()


def get_candidate_for_surplus(root):
    candidates = sorted(root.get_children(), key=lambda x: -x.weight)
    for idx, group in enumerate(candidates):
        print candidates[:idx]
        if group.demand == 0:
            break

get_candidate_for_surplus(groups['group_atlas']['prod'])
