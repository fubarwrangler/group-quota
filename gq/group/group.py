# *****************************************************************************
# Group class used for Group-tree creation
# *****************************************************************************

import logging
from collections import deque

log = logging.getLogger()

__all__ = ['AbstractGroup', 'DemandGroup', 'QuotaGroup']


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

    def breadth_first(self):
        """ Walk through tree breadth-first (all nodes on a level before descent) """
        q = deque()
        q.append(self)
        while q:
            result = q.popleft()
            yield result

            if not result.is_leaf:
                for c in result.get_children():
                    q.append(c)

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
        """ Find a group named @name below self """
        for x in self.all():
            if name == x.full_name:
                return x
        return None

    def leaf_nodes(self):
        return (x for x in self if x.is_leaf)

    def print_tree(self, n=0):
        print '|' + '--' * (n) + str(self)
        for child in sorted(self.get_children(), key=lambda x: x.name):
            child.print_tree(n + 1)

    def __getitem__(self, key):
        return self.children[key]

    def __repr__(self):
        return '<0x%x> %s' % (id(self), self.full_name)

    def __iter__(self):
        return iter(self.walk())

    def __contains__(self, key):
        return (len([x.full_name for x in self if x.full_name == key]) > 0)

    def __str__(self):
        return self.full_name


class DemandGroup(AbstractGroup):

    def __init__(self, name, weight=1.0, accept_surplus=False, surplus_threshold=0):
        super(DemandGroup, self).__init__(name)

        self.accept = bool(accept_surplus)
        self.threshold = surplus_threshold
        self.weight = weight

        self.demand = 0

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
        grpcolor = '\033[96m' if self.accept else '\033[94m'
        return '%s%s\033[0m: surplus \033[93m%s\033[0m, weight %f,' \
               ' threshold %d demand \033[33m%d\033[0m' % \
               (grpcolor, '(%s)' % n + self.name, self.accept, self.weight,
                self.threshold, self.demand)

    def color_str(self):
        p = self
        depth = -1
        while p.parent:
            p = p.parent
            depth += 1
        return '+' + '--' * depth + str(self)


class QuotaGroup(AbstractGroup):

    def __init__(self, name, quota=0, priority=10.0, accept_surplus=False):
        super(QuotaGroup, self).__init__(name)

        self.quota = int(quota)
        self.prio = float(priority)
        self.surplus = str(bool(accept_surplus)).upper()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "'%s' - quota=%d - prio=%.1f - surplus=%s" % \
               (self.full_name, self.quota, self.prio, self.surplus)

    def diff(self, other):
        diffs = list()
        for x in ("full_name", "quota", "prio", "surplus"):
            if getattr(self, x) != getattr(other, x):
                diffs.append(x)
        return diffs

    def full_cmp(self, other):
        my_names = set([x.full_name for x in self.all()])
        other_names = set([x.full_name for x in other.all()])

        if set(my_names) ^ set(other_names):
            return False

        return all([x == y for x, y in zip(self.all(), other.all())])

    def __eq__(self, other):
        return not self.diff(other)

    def __ne__(self, other):
        return self.diff(other)
