#!/usr/bin/python

import logging

from group.db import build_groups_db, update_surplus_flags
import demand.idlejobs


from log import setup_logging

log = setup_logging('/foo', backup=1, size_mb=20, level=logging.INFO)


def turn_surplus_flag(groups, val):
    for g in groups:
        log.debug("%s accept=%s", g.full_name, val)
        g.accept = val


def calculate_surplus(root):

    log.debug("*********************  Get Candidates  **********************")

    for group in (x for x in root.all() if not x.is_leaf):

        # Candidates are the children of the intermediate groups in DFS order
        candidates = sorted(group.get_children(), key=lambda x: -x.weight)

        log.debug("Sibling group -- children of %s", group.full_name)

        already_set = False

        # Weights in descending order
        for weight in sorted(set(g.weight for g in candidates), reverse=True):
            # All groups with same weight get same treatment
            groups = [x for x in candidates if x.weight == weight]
            my_demand = any([x.has_demand() for x in groups])

            lower_groups = [x for x in candidates if 0 < x.weight < weight]

            lower_demand = any([x for x in lower_groups if x.has_demand()])
            log.debug("%s -- lower groups=%s, demand=%s, l_demand=%s",
                      ", ".join(x.full_name for x in groups),
                      ", ".join(x.full_name for x in lower_groups),
                      my_demand, lower_demand)

            if (not my_demand and lower_demand) or already_set:
                turn_surplus_flag(groups, False)
            else:
                turn_surplus_flag(groups, True)
                already_set = True

    # Go through again and turn off non-leaf intermediate nodes that don't
    # have slack from their neighbors, just to prevent toggling too much
    for group in root.all():
        all_leaf = all([x.is_leaf for x in group.siblings()])
        slack = any([x.has_slack() for x in group.siblings()])
        if group.accept and not slack and not all_leaf:
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

groups.print_tree()

# scn_full_analysis(groups)
# scn_no_analysis(groups)
# scn_no_atlas(groups)
# scn_no_prod(groups)
# scn_asym_analysys(groups)


groups.group_grid.demand = 11
groups.group_grid.threshold = 10

calculate_surplus(groups)

groups.print_tree()

update_surplus_flags(groups)
