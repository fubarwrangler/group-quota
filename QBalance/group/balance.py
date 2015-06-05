# *****************************************************************************

import logging

log = logging.getLogger()

__all__ = ['calculate_surplus']


def turn_surplus_flag(groups, val):
    for g in groups:
        log.info("%s accept=%s", g.full_name, val)
        g.accept = val


def calculate_surplus(root):
    """ This is the core balancing algorithm for figuring out which group
        get the accept_surplus flag
    """

    log.debug("*********************  Get Candidates  **********************")

    for group in (x for x in root.all() if not x.is_leaf):

        # Candidates are the children of the intermediate groups in DFS order
        candidates = sorted(group.get_children(), key=lambda x: -x.weight)

        log.info("Sibling group -- children of %s", group.full_name)

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
        slack = any([x.has_slack() for x in group.siblings() if x.weight > 0])
        if group.accept and not slack and not all_leaf:
            log.info("%s (intermediate and no weighted slack) toggle t->f",
                     group.full_name)
            group.accept = False
