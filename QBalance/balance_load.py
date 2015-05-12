#!/usr/bin/python

import logging

from group.db import build_groups_db
import demand.idlejobs


from log import setup_logging

log = setup_logging('/foo', backup=1, size_mb=20, level=logging.INFO)
groups = build_groups_db()


def set_surplus_all_leaves(siblings):

    log.debug("All-leaf group: %s", ", ".join((x.full_name for x in siblings)))

    for idx, group in enumerate(siblings):

        lower_groups = [x for x in siblings if 0 < x.weight < group.weight]

        # any lower queues with demand or slack?
        lower_demand = any([x for x in lower_groups if x.has_demand()])

        log.debug("%s -- lower groups = %s", group.full_name,
                  ", ".join((x.full_name for x in lower_groups)))
        log.debug("%s lower_demand=%s", group.full_name, lower_demand)
        if not group.has_demand() and lower_demand:
            group.accept = False
        else:
            group.accept = True


def set_surplus_other(siblings):
    #lower_slack = any([x for x in lower_groups if x.has_slack()])
    pass


def set_surplus(root):
    log.debug("*********************  Get Candidates  **********************")

    for group in (x for x in root.all() if not x.is_leaf):

        log.debug("Sibling group -- children of %s", group.full_name)
        candidates = sorted(group.get_children(), key=lambda x: -x.weight)
        if all(x.is_leaf for x in candidates):
            set_surplus_all_leaves(candidates)
        else:
            set_surplus_other(candidates)


demand.idlejobs.populate(groups)

groups.print_tree()

set_surplus(groups)

groups.print_tree()
