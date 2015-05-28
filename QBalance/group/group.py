# *****************************************************************************
# Group class used for Group-tree creation
# *****************************************************************************

import logging

log = logging.getLogger()


class AbstractGroup(object):
    """ A tree of scheduling groups. Leaf nodes are groups where jobs are
        actually submitted, mid-level nodes set limits on the surplus-sharing
        abilities of this tree of groups.
    """
    def __init__(self, name):
        self.name = name

        self.parent = None
        self.children = {}

    def add_child(self, new_grp):
        """ Add a child node to this one, setting it's parent pointer """

        new_grp.parent = self
        self.children[new_grp.name] = new_grp

    def walk(self):
        """ Recursively iterate through all lower nodes in the tree DFS order """
        for x in self.get_children():
            for y in x.walk():
                yield y
            yield x

    def all(self):
        """ Like walk() but include self in list returned """
        for x in self.get_children():
            for y in x.walk():
                yield y
            yield x
        yield self

    def siblings(self):
        """ Siblings are *all* your parent's children, self included """
        if self.parent:
            return self.parent.get_children()
        else:
            return {}

    @property
    def full_name(self):
        """ Walk up tree to form fqdn for group, except for implicit <root> """
        if not self.parent:
            return self.name

        names = list()
        parent = self
        while parent is not None:
            names.append(parent.name)
            parent = parent.parent
        return ".".join(reversed(names[:-1]))

    @property
    def is_leaf(self):
        return (not self.children)

    def get_children(self):
        """ Return list of all children group-objects """
        return self.children.itervalues()

    def find(self, name):
        """ Find a group named @name below self -- raise Exception """
        if self.name == name:
            return self
        for x in self.walk():
            if name == x.name:
                return x
        raise Exception("No group %s found" % name)

    def leaf_nodes(self):
        return (x for x in self if x.is_leaf)

    def print_tree(self, n=0):
        print '|' + '--' * (n) + str(self)
        for child in sorted(self.get_children(), key=lambda x: x.name):
            child.print_tree(n + 1)

    def __getitem__(self, key):
        return self.children[key]

    def __getattr__(self, name):
        if name in self.children:
            return self.children[name]
        raise AttributeError

    def __repr__(self):
        return '<0x%x> %s' % (id(self), self.full_name)

    def __iter__(self):
        return iter(self.walk())

    def __contains__(self, key):
        return (len([x.name for x in self if x.name == key]) > 0)

    def __str__(self):
        return self.full_name


class DemandGroup(AbstractGroup):

    def __init__(self, name, weight=1, surplus=False, threshold=0, running=0):
        super(DemandGroup, self).__init__(name)

        self.accept = bool(surplus)
        self.running = running
        self.threshold = threshold
        self.weight = weight

        self.demand = 0
        log.debug("Create group: %s", self)

    def has_demand(self):
        if self.is_leaf:
            return self.weight > 0 and self.demand > self.threshold
        else:
            return self.weight > 0 and any(x.has_demand() for x in self.get_children())

    def has_slack(self):
        if self.is_leaf:
            return self.weight == 0 or self.demand <= self.threshold
        else:
            return self.weight > 0 and all(x.has_slack() for x in self.get_children())

    def __str__(self):
        n = 'D' if self.has_demand() else '' + 'S' if self.has_slack() else ''
        return '\033[94m%s\033[0m: surplus \033[93m%s\033[0m, weight %f,' \
               ' threshold %d demand %d' % \
               ('(%s)' % n + self.name, self.accept, self.weight, self.threshold,
                self.demand)

    def color_str(self):
        p = self
        d = -1
        while p.parent:
            p = p.parent
            d += 1

        n = 'D' if self.has_demand() else '' + 'S' if self.has_slack() else ''
        return ' '*d + '\033[94m%s\033[0m: surplus \033[93m%s\033[0m, weight %f,' \
               ' threshold %d demand %d' % \
               ('(%s)' % n + self.name, self.accept, self.weight, self.threshold,
                self.demand)


class QuotaGroup(AbstractGroup):

    def __init__(self, name, quota=0, prio=10.0, surplus=False):
        super(QuotaGroup, self).__init__(name)

        self.quota = int(quota)
        self.prio = float(prio)
        self.surplus = str(bool(surplus)).upper()

    def __str__(self):
        msg = '\n'
        msg += 'GROUP_QUOTA_%s = %d\n' % (self.name, self.quota)
        msg += 'GROUP_PRIO_FACTOR_%s = %.1f\n' % (self.name, self.prio)
        msg += 'GROUP_ACCEPT_SURPLUS_%s = %s\n' % (self.name, self.surplus)
        return msg

    def diff(self, other):
        diffs = list()
        for x in ("full_name", "quota", "prio", "surplus"):
            if getattr(self, x) != getattr(other, x):
                diffs.append(x)
        return diffs

    def __repr__(self):
        return "'%s' - quota=%d - prio=%.1f - surplus=%s" % \
               (self.name, self.quota, self.prio, self.surplus)

    def __cmp__(self, other):

        same = True
        for x in ("full_name", "quota", "prio", "surplus"):
            if getattr(self, x) != getattr(other, x):
                same = False
                break
        if same:
            return 0
        else:
            return 1 if self.full_name >= other.full_name else -1
