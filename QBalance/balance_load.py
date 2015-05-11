#!/usr/bin/python

import logging

from group.db import build_groups_db
import demand.idlejobs


from log import setup_logging

log = setup_logging('/foo', backup=1, size_mb=20, level=logging.INFO)
groups = build_groups_db()


def get_candidate_for_surplus(root):
    log.debug("************************** Get Candidates **************************")

    for group in (x for x in root.all() if not x.is_leaf):
        log.debug("Sibling group -- children of %s", group.full_name)
        candidates = sorted(group.get_children(), key=lambda x: -x.weight)

        all_leaf = all(x.is_leaf for x in candidates)

        for child in candidates:
            lower_groups = [x for x in candidates if x.weight < child.weight]

            if child.demand < child.threshold:
                if any([x for x in lower_groups if x.demand > x.threshold]):
                    log.debug("Demand for %s below threshold AND lower groups "
                              "have demand, set to FALSE", child.full_name)
                    child.accept = False
                    continue
            else:
                if all_leaf:
                    pass
                log.debug("%s has demand, set to TRUE", child.full_name)
                child.accept = True
                break


demand.idlejobs.populate(groups)

groups.print_tree()

get_candidate_for_surplus(groups)

groups.print_tree()
