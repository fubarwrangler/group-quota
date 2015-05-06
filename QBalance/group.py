# *****************************************************************************
# Group class used for Group-tree creation
# *****************************************************************************


class Group(object):
    """ A tree of scheduling groups. Leaf nodes are groups where jobs are
        actually submitted, mid-level nodes set limits on the surplus-sharing
        abilities of this tree of groups.
    """

    def __init__(self, name, weight=1, surplus=False, threshold=0, running=0):
        # These variables define the nature of the group, and are explicitly set
        self.name = name
        self.accept_surplus = surplus
        self.running = running
        self.threshold = threshold
        self.weight = weight

        self.parent = None
        self.children = {}

    def add_child(self, group):
        """ Add a child node to this one, setting it's parent pointer """

        print "Adding child %s to %s" % (group.name, self.name)

        group.parent = self
        self.children[group.name] = group

    @property
    def full_name(self):
        names = list()
        parent = self
        while parent is not None:
            names.append(parent.name)
            parent = parent.parent
        return ".".join(reversed(names[:-1]))

    def walk(self):
        """ Recursively iterate through all lower nodes in the tree """
        if not self.children:
            return
        for x in self.children.values():
            yield x
            for y in x.walk():
                yield y

    def get_children(self):
        return self.children.values()

    def find(self, name):
        if self.name == name:
            return self
        for x in self.walk():
            if name == x.name:
                return x
        raise Exception("No group %s found" % name)

    def names(self):
        return (x.name for x in self)

    def active_groups(self):
        """ Active groups are leaf nodes -- i.e. nodes without children """
        return (x for x in self if not x.children)

    def print_tree(self, n=0):
        print '|' + '--'*(n) + self.name
        for child in sorted(self, key=lambda x: x.name):
            child.print_tree(n + 1)

    def __getitem__(self, key):
        return self.children[key]

    def __repr__(self):
        return '<0x%x> %s (%d)' % (id(self), self.name, self.quota)

    def __iter__(self):
        return iter(self.walk())

    def __contains__(self, key):
        return (len([x.name for x in self if x.name == key]) > 0)

    def __str__(self):
        return '%s: surplus %s, weight %f, threshold %d' % \
               (self.name, self.accept_surplus, self.weight, self.threshold)
