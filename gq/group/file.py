import logging
import sys
import re

import group

log = logging.getLogger()


class NoQuotaFile(Exception):
    pass


def build_quota_groups_file(fname, grpCLS=group.QuotaGroup):

    root = grpCLS('<root>')

    try:
        group_names, grps = _read_quotas(fname)
    except NoQuotaFile:
        log.info("Quota file %s not found, return blank group-tree", fname)
        return root

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


def read_lines_continue(fobj):
    """ Continue lines that end in backslash """

    in_line = False
    tmp = ''
    for line in (x.strip() for x in fobj if x):
        if re.match(r'^\s*#', line):
            continue

        if line.endswith('\\'):
            tmp += line.rstrip('\\')
            in_line = True
            continue
        elif in_line:
            in_line = False
            line = tmp + line.rstrip('\\')
            tmp = ''

        yield line


def _read_quotas(fname):
    try:
        fp = open(fname, "r")
    except EnvironmentError, e:
        if e.errno == 2:
            raise NoQuotaFile
        log.error("Error opening %s: %s", fname, e)
        sys.exit(1)

    regexes = {
        "names":   re.compile(r'^GROUP_NAMES\s*=\s*(\$\(GROUP_NAMES\))?(.*)$'),
        "quota":   re.compile(r'^GROUP_QUOTA_([\w\.]+)\s*=\s*(\d+)$'),
        "prio":    re.compile(r'^GROUP_PRIO_FACTOR_([\w\.]+)\s*=\s*([\d\.]+)$'),
        "surplus": re.compile(r'^GROUP_ACCEPT_SURPLUS_([\w\.]+)\s*=\s*(\w+)$'),
    }

    grps = {}
    group_names = []
    for line in read_lines_continue(fp):

        for kind, regex in regexes.items():
            if not regex.match(line):
                continue
            if kind == "names":
                group_names = regex.match(line).group(2).replace(' ', '').split(',')
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

    return group_names, grps
