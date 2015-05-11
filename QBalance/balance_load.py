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
        for child in candidates:
            lower_groups = [x for x in candidates if x.weight < child.weight]
            log.debug("Lower groups for %s: %s", child.full_name,
                      ", ".join([x.full_name for x in lower_groups]))

            if child.demand < child.threshold:
                if any([x for x in lower_groups if x.demand > x.threshold]):
                    child.accept = False
                    continue
            else:
                child.accept = True
                break


demand.idlejobs.populate(groups)

groups.print_tree()

get_candidate_for_surplus(groups)

groups.print_tree()
