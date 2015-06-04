#!/usr/bin/python
import logging
from log import setup_logging

log = setup_logging(None, backup=1, size_mb=20, level=logging.DEBUG)

from group.db import build_demand_groups_db, update_surplus_flags
from group.idlejobs import populate_demand
from group.balance import calculate_surplus


def scn_asym_analysys(groups):
    groups.group_atlas.analysis.short.demand = 0
    groups.group_atlas.analysis.long.demand = 6000
    groups.group_atlas.analysis.demand = 6000


def scn_no_analysis(groups):
    groups.group_atlas.analysis.short.demand = 0
    groups.group_atlas.analysis.long.demand = 0
    groups.group_atlas.analysis.demand = 0


def scn_full_analysis(groups):
    groups.group_atlas.analysis.short.demand = 6000
    groups.group_atlas.analysis.long.demand = 6000
    groups.group_atlas.analysis.demand = 6000


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


groups = build_demand_groups_db()

populate_demand(groups)

groups.print_tree()

# scn_full_analysis(groups)
# scn_no_analysis(groups)
# scn_no_atlas(groups)
scn_no_prod(groups)
scn_asym_analysys(groups)


groups.group_grid.demand = 11
groups.group_grid.threshold = 10

calculate_surplus(groups)

groups.print_tree()

# update_surplus_flags(groups)
