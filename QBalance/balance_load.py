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

    for group in itertools.chain((x for x in root if not x.is_leaf), [root]):
        log.debug("Sibling group -- children of %s", group.full_name)
        candidates = sorted(group.get_children(), key=lambda x: -x.weight)
        for idx, child in enumerate(candidates):
            lower_groups = candidates[idx+1:]
            log.debug(" * %s", child)
            log.debug(candidates[idx+1:])
            #if child.demand == 0:
            #    break



demand.idlejobs.populate(groups)

get_candidate_for_surplus(groups)
