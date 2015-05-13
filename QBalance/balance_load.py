#!/usr/bin/python

import logging

from group.db import build_groups_db
import demand.idlejobs


from log import setup_logging

log = setup_logging('/foo', backup=1, size_mb=20, level=logging.INFO)


def group_by(g, val):
    ov = None
    l = list()
    for n, i in enumerate(g):
        v = getattr(i, val)
        if v != ov and ov is not None:
            yield l
            l = list()
        l.append(i)
        ov = v
    yield l


def surplus_logic(leaf, lower_slack, lower_demand, jobs):
    # ((~d | j) & l) | (~l & s)
    if (leaf and (jobs or not lower_demand)) or (not leaf and lower_slack):
        log.debug("--> l & (j | !d) OR !l & s = OK")
        return True
    else:
        log.debug("--> Fail - FALSE")
        return False


def set_surplus(root):
    log.debug("*********************  Get Candidates  **********************")

    for group in (x for x in root.all() if not x.is_leaf):

        log.debug("Sibling group -- children of %s", group.full_name)
        candidates = sorted(group.get_children(), key=lambda x: -x.weight)

        for equal_grouping in group_by(candidates, 'weight'):
            g = equal_grouping[0]
            lower_groups = [x for x in candidates if 0 < x.weight < g.weight]

            # Are we an all-leaf group?
            all_leaf = all([x.is_leaf for x in candidates])

            # any lower queues with demand or slack?
            lower_slack = any([x for x in lower_groups if x.has_slack()])
            lower_demand = any([x for x in lower_groups if x.has_demand()])

            log.debug("%s -- lower groups = %s", g.full_name,
                      ", ".join((x.full_name for x in lower_groups)))
            log.debug("%s lower_demand=%s, lower_slack=%s, all_leaf=%s",
                      g.full_name, lower_demand, lower_slack, all_leaf)
            if surplus_logic(all_leaf, lower_slack, lower_demand, g.real_demand()):
                for grp in equal_grouping:
                    grp.accept = True
                break
            for grp in equal_grouping:
                grp.accept = False


groups = build_groups_db()

demand.idlejobs.populate(groups)
groups['group_atlas']['analysis']['short'].demand = 0
groups['group_atlas']['analysis']['long'].demand = 0
groups['group_atlas']['analysis'].demand = 0
#groups['group_atlas']['prod']['mp'].demand = 0
groups['group_grid'].demand = 1
groups['group_grid'].threshold = 10
groups.print_tree()

set_surplus(groups)

groups.print_tree()
