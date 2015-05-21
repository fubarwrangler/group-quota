#!/usr/bin/python

import logging

from group.db import build_groups_db
import demand.idlejobs


from log import setup_logging

log = setup_logging('/foo', backup=1, size_mb=20, level=logging.INFO)


def set_equal(group, groups, val):
    for g in (x for x in groups if x.weight == group.weight):
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
            g = [x for x in candidates if x.weight == w][0]

            lower_groups = [x for x in candidates if 0 < x.weight < w]
            lower_demand = any([x for x in lower_groups if x.has_demand()])
            log.debug("%s -- lower groups = %s", g.full_name,
                      ", ".join((x.full_name for x in lower_groups)))
            log.debug("%s slack=%s l_demand=%s", g.full_name, g.has_slack(), lower_demand)

            if (g.has_slack() and lower_demand) or already_set:
                if all_leaf and not already_set:
                    set_equal(g, candidates, True)
                    already_set = True
                else:
                    set_equal(g, candidates, False)
            else:
                set_equal(g, candidates, True)
                already_set = True


groups = build_groups_db()

demand.idlejobs.populate(groups)
# groups['group_atlas']['analysis']['short'].demand = 0
# groups['group_atlas']['analysis']['long'].demand = 0
# groups['group_atlas']['analysis'].demand = 0
# groups['group_atlas']['prod']['mp'].demand = 0
groups['group_grid'].demand = 1
groups['group_grid'].threshold = 10
groups.print_tree()

set_surplus(groups)

groups.print_tree()
