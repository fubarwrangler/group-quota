# *****************************************************************************
# Group class used for Group-tree creation
# *****************************************************************************


class Group(object):
    """ A tree of scheduling groups. Leaf nodes are groups where jobs are
        actually submitted, mid-level nodes set limits on the surplus-sharing
        abilities of this tree of groups.
    """

    def __init__(self, name, weight=1, surplus=False, threshold=0, running=0):
        self.name = name
        self.accept = bool(surplus)
        self.running = running
        self.threshold = threshold
        self.weight = weight

        self.parent = None
        self.children = {}
        self.demand = 0

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
        n = 'D' if self.has_demand() else '' + 'S' if self.has_slack() else ''
        return '\033[94m%s\033[0m: surplus \033[93m%s\033[0m, weight %f,' \
               ' threshold %d demand %d' % \
               ('(%s)' % n + self.name, self.accept, self.weight, self.threshold,
                self.demand)
