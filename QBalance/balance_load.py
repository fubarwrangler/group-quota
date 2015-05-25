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
            my_demand = any([x.has_demand() for x in groups])

            lower_groups = [x for x in candidates if 0 < x.weight < w]
            log.debug([(x.full_name, x.has_slack()) for x in lower_groups])

            lower_demand = any([x for x in lower_groups if x.has_demand()])
            log.debug("%s -- lower groups = %s", groups,
                      ", ".join((x.full_name for x in lower_groups)))
            log.debug("%s demand=%s l_demand=%s", groups, my_demand, lower_demand)

            if (not my_demand and lower_demand) or already_set:
                set_equal(groups, False)
            else:
                set_equal(groups, True)
                already_set = True

    # Go through again and turn off certain non-leaf intermediate nodes
    for group in root.all():
        all_leaf = all([x.is_leaf for x in group.siblings()])
        no_slack = not any([x.has_slack() for x in group.siblings()])
        if group.accept and no_slack and not all_leaf:
            log.debug("%s toggle t->f", group.full_name)
            group.accept = False


def scn_asym_analysys(groups):
    groups.group_atlas.analysis.short.demand = 0
    groups.group_atlas.analysis.long.demand = 251
    groups.group_atlas.analysis.demand = 251


def scn_no_analysis(groups):
    groups.group_atlas.analysis.short.demand = 0
    groups.group_atlas.analysis.long.demand = 0
    groups.group_atlas.analysis.demand = 0


def scn_full_analysis(groups):
    groups.group_atlas.analysis.short.demand = 1000
    groups.group_atlas.analysis.long.demand = 1000
    groups.group_atlas.analysis.demand = 1000


def scn_no_mcore(groups):
    groups.group_atlas.prod.mp.demand = 0
    scn_full_analysis(groups)


def scn_no_prod(groups):
    for x in groups.group_atlas.prod.all():
        x.demand = 0
    scn_full_analysis(groups)

    # scn_full_analysis(groups)


def scn_no_mcore_or_himem(groups):
    groups.group_atlas.prod.mp.demand = 0
    groups.group_atlas.prod.test.demand = 0
    scn_full_analysis(groups)


def scn_no_atlas(groups):
    for g in groups.group_atlas.all():
        g.demand = 0


groups = build_groups_db()

demand.idlejobs.populate(groups)

# scn_full_analysis(groups)
# scn_no_analysis(groups)
# scn_no_atlas(groups)
# scn_no_prod(groups)
scn_asym_analysys(groups)


groups.group_grid.demand = 11
groups.group_grid.threshold = 10

set_surplus(groups)

groups.print_tree()
