#!/usr/bin/python

import logging

from group.db import build_groups_db
import demand.idlejobs


from log import setup_logging

log = setup_logging('/foo', backup=1, size_mb=20, level=logging.INFO)


def set_equal(groups, val):
    for g in groups:
        log.debug("%s accept=%s", g.full_name, val)
        g.accept = val


def set_surplus(root):
    log.debug("*********************  Get Candidates  **********************")

    for group in (x for x in root.all() if not x.is_leaf):

        candidates = sorted(group.get_children(), key=lambda x: -x.weight)

        already_set = False
        all_leaf = all([x.is_leaf for x in candidates])
        log.debug("Sibling group -- children of %s, all_leaf=%s",
                  group.full_name, all_leaf)

        for w in sorted(set(g.weight for g in candidates), reverse=True):
            groups = [x for x in candidates if x.weight == w]
            any_slack = any([x.has_slack() for x in candidates])

            lower_groups = [x for x in candidates if 0 < x.weight < w]
            lower_demand = any([x for x in lower_groups if x.has_demand()])
            log.debug("%s -- lower groups = %s", groups,
                      ", ".join((x.full_name for x in lower_groups)))
            log.debug("%s slack=%s l_demand=%s", groups, any_slack, lower_demand)

            if (any_slack and lower_demand) or already_set:
                if all_leaf and not already_set:
                    log.debug('Would be false, but leaf so true!')
                    set_equal(groups, True)
                    already_set = True
                else:
                    set_equal(groups, False)
            else:
                if not all_leaf and not any_slack:
                    log.debug('Would be true, but non-leaf & no slack so false!')
                    set_equal(groups, False)
                else:
                    set_equal(groups, True)
                    already_set = True


def scn1(groups):
    groups['group_atlas']['analysis']['short'].demand = 0
    groups['group_atlas']['analysis']['long'].demand = 251
    groups['group_atlas']['analysis'].demand = 251


def scn2(groups):
    groups['group_atlas']['analysis']['short'].demand = 0
    groups['group_atlas']['analysis']['long'].demand = 0


def scn3(groups):
    groups['group_atlas']['analysis'].demand = 1000
    groups['group_atlas']['analysis']['short'].demand = 1000
    groups['group_atlas']['analysis']['long'].demand = 1000


def scn4(groups):
    groups['group_atlas']['prod']['mp'].demand = 0

groups = build_groups_db()

demand.idlejobs.populate(groups)

scn1(groups)

groups['group_grid'].demand = 11
groups['group_grid'].threshold = 10
groups.print_tree()

set_surplus(groups)

groups.print_tree()
