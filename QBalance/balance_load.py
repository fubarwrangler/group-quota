#!/usr/bin/python

import logging

from group.db import build_groups_db
import demand.idlejobs


from log import setup_logging

log = setup_logging('/foo', backup=1, size_mb=20, level=logging.INFO)
groups = build_groups_db()


def set_surplus(root):
    log.debug("*********************  Get Candidates  **********************")

    for group in (x for x in root.all() if not x.is_leaf):
        log.debug("Sibling group -- children of %s", group.full_name)
        candidates = sorted(group.get_children(), key=lambda x: -x.weight)

        all_leaf = all(x.is_leaf for x in candidates)

        for child in candidates:
            lower_groups = [x for x in candidates if x.weight < child.weight]

            # any lower queues with demand or slack?
            lower_demand = any([x for x in lower_groups if x.has_demand()])
            lower_slack = any([x for x in lower_groups if x.has_slack()])

            if child.has_demand():
                log.debug("%s has demand, set to TRUE if (slack & !leaf)|demand",
                          child.full_name)
                log.debug("%s all_leaf=%s, lower_slack=%s, lower_demand=%s",
                          child.full_name, all_leaf, lower_slack, lower_demand)

                if (lower_slack and not all_leaf) or lower_demand:
                    log.debug("%s - set to TRUE", child.full_name)
                    child.accept = True
                    continue
                else:
                    log.debug("%s - set to FALSE", child.full_name)
                    child.accept = False

            else:
                log.debug("Demand for %s below threshold AND lower groups "
                          "have demand, set to FALSE", child.full_name)
                child.accept = False
                break


demand.idlejobs.populate(groups)

groups.print_tree()

set_surplus(groups)

groups.print_tree()
