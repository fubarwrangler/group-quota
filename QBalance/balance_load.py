#!/usr/bin/python

import logging
import itertools

from group.db import build_groups_db
import demand.idlejobs


from log import setup_logging

log = setup_logging('/foo', backup=1, size_mb=20, level=logging.INFO)
groups = build_groups_db()


def get_candidate_for_surplus(root):
    log.debug("************************** Get Candidates **************************")

    # visited = list()

    for group in itertools.chain((x for x in root if not x.is_leaf), [root]):
        # if group in visited:
        #    continue

        log.debug("Sibling group -- children of %s", group.full_name)
        for child in group.get_children():
            # visited.append(child)
            log.debug(" * %s", child.full_name)

    return

    candidates = sorted(root.get_children(), key=lambda x: -x.weight)
    for idx, group in enumerate(candidates):
        print repr(group)
        if group.demand == 0:
            break


demand.idlejobs.populate(groups)

get_candidate_for_surplus(groups)
