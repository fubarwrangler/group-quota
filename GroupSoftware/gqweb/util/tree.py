# ===========================================================================
# Functions to check tree modifications, adding/removing/quota-change and
# so on.
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from ..application import app

from validation import group_defaults
from ..db.models import build_group_tree_formdata


def set_quota_sums(db, root):
    """ Renormalize the sums in the group-tree (@root) of non-leaf nodes

        @db: a db-query list of all groups to search for ORM-mapped objects in
        @root: the root of the tree-object with the modified sums in it
    """
    for group in root:
        if group.is_leaf:
            continue

        newquota = sum(x.quota for x in group.get_children())

        # NOTE: Auth here is done by role-based auth
        if newquota != group.quota:
            app.logger.debug("Intermediate group sum %s: %d->%d",
                             group.full_name, group.quota, newquota)
            dbobj = next(x for x in db if x.group_name == group.full_name)
            dbobj.quota = newquota
            group.quota = newquota

        # If newly added group causes a former leaf that has non-zero
        # threshold to become a non-leaf then set it to zero!
        if group.surplus_threshold > 0:
            dbobj = next(x for x in db if x.group_name == group.full_name)
            dbobj.surplus_threshold = 0


def remove_groups(candidates, tree):
    """ Test which groups can be removed from the tree and return any that
        break the tree-layout (would strand nodes without a parent)

        @candidates: a set() or list of candidate group-names
        @tree: the tree object to check @candidates against
    """
    bad_removes = list()
    warned = set()
    for group in (tree.find(x) for x in candidates):
        stranded = set(x.full_name for x in group) - candidates
        if stranded - warned:
            bad_removes.append((group.full_name, stranded - warned))
        warned |= stranded
    return bad_removes


def new_group_fits(data, tree):
    """ See if the new-group defined by @data fits into the existing @tree

        @data: a dictionary with the new-group's data in key-value pairs
        @tree: the tree object to check against
    """

    newname = data['group_name']
    if tree.find(newname):
        return "Group %s already exists" % newname

    if newname.count('.') >= 1:
        parent = ".".join(newname.split('.')[:-1])
        if not tree.find(parent):
            return "New group <strong>%s</strong> must have" \
                   " a parent in the tree (<u>%s</u>)" % \
                   (newname, parent)

    missing_fields = set(group_defaults) - set(data)
    if missing_fields:
        misslist = ", ".join(sorted(missing_fields))
        return "New group needs the following fields defined: %s" % misslist


def set_params(db, formdata):
    """ Populate database objects in @db with user-input from @formdata """

    for name, params in formdata.iteritems():
        dbobj = next(x for x in db if x.group_name == name)
        for param, val in params.iteritems():
            if param == 'group_name' or param == 'new_name':
                continue
            if (isinstance(val, float) and abs(val - float(getattr(dbobj, param))) > 0.1) \
               or not isinstance(val, float):
                setattr(dbobj, param, val)

        # NOTE: Since form value isn't present if not checked!
        dbobj.accept_surplus = 'accept_surplus' in params


def set_renames(db, formdata):
    """ Detect renamed groups and fix them in the DB accordingly

        @db: database objects from query to modify
        @formdata: dictionary of dictionaries from form input
    """

    def gen_tree_list(form):
        treelist = list(build_group_tree_formdata(formdata))
        return sorted(treelist, key=lambda x: x.full_name)

    root = gen_tree_list(formdata)
    existing_names = set(x.full_name for x in root)
    clean_root = gen_tree_list(formdata)

    # NOTE: Two copies needed for this traversal because we modify the first
    #       copy as we go in alphabetical order to allow renames to propogate
    #       correctly.
    for group, orig_grp in zip(root, clean_root):
        params = formdata[orig_grp.full_name]

        # Detect lowest-level changes in group name
        old = orig_grp.full_name.split('.')[-1]
        new = params.get('new_name', old)
        if old != new:
            # This will propogate through the tree if the group has children
            group.rename(new)

            if group.full_name in existing_names:
                raise ValueError("Multiple groups named %s found!" % group.full_name)

        # Find db-object that matches old name and rename it to match the
        # possibly modified group-tree
        obj = next(x for x in db if x.group_name == orig_grp.full_name)
        if obj.group_name != group.full_name:
            app.logger.debug("Group rename detected!: %s->%s",
                             obj.group_name, group.full_name)
            obj.group_name = group.full_name

    app.logger.debug("\n".join(map(str, root)))
