import logging
import sys
import re

import group

log = logging.getLogger()


def build_quota_groups_file(fname, grpCLS=group.QuotaGroup):

    root = grpCLS('<root>')

    try:
        fp = open(fname, "r")
    except IOError, e:
        log.error("Error opening %s: %s", fname, e)
        sys.exit(1)

    regexes = {
        "names":   re.compile('^GROUP_NAMES\s*=\s*(.*)$'),
        "quota":   re.compile('^GROUP_QUOTA_([\w\.]+)\s*=\s*(\d+)$'),
        "prio":    re.compile('^GROUP_PRIO_FACTOR_([\w\.]+)\s*=\s*([\d\.]+)$'),
        "surplus": re.compile('^GROUP_ACCEPT_SURPLUS_([\w\.]+)\s*=\s*(\w+)$'),
        }

    grps = {}
    group_names = []
    for line in (x.strip() for x in fp if x and not re.match('^\s*#', x)):

        for kind, regex in regexes.items():
            if not regex.match(line):
                continue
            if kind == "names":
                group_names = regex.match(line).group(1).replace(' ', '').split(',')
            else:
                grp, val = regex.match(line).groups()
                if not grps.get(grp):
                    grps[grp] = {}
                if kind == "surplus":
                    if val.upper() == "TRUE":
                        val = True
                    elif val.upper() == "FALSE":
                        val = False
                    else:
                        log.error("Invalid true/false value found: %s", val)
                        sys.exit(1)
                grps[grp][kind] = val
    fp.close()

    for grp in sorted(group_names):

        p = grps.get(grp, None)
        if p is None or not ("quota" in p and "prio" in p and "surplus" in p):
            log.error("Invalid incomplete file-group found: %s", grp)
            sys.exit(1)

        parts = grp.split('.')
        my_name = parts[-1]

        # Find appropriate parent from string of full group-name
        parent = root
        for x in parts[:-1]:
            try:
                parent = parent[x]
            except KeyError:
                log.error("%s without parent found in DB", grp)
                sys.exit(1)

        new = group.QuotaGroup(my_name, p["quota"], p["prio"], p["surplus"])
        parent.add_child(new)

    return root
