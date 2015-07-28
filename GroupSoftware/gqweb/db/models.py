# ===========================================================================
# Database model and tree-object with HTML hooks from group-class and info
# about field-types and validation methods used for form data
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
import hashlib

from group.group import AbstractGroup
from group.db import _build_groups_db

from .. import app

from sqlalchemy import Table
from database import Base


class Group(Base):
    __table__ = Table(app.config['TABLE_NAME'], Base.metadata, autoload=True)


class GroupTree(AbstractGroup):
    def __init__(self, name, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        super(GroupTree, self).__init__(name)

    @property
    def full_html(self):
        s = self.full_name.split('.')
        first, last = '.'.join(s[:-1]) + "." if len(s) > 1 else '', s[-1]
        return "%s<u>%s</u>" % (first, last)

    def group_order(self):
        for x in (x for x in self.all() if not x.is_leaf):
            yield x.children.values()

    def rename(self, new):
        self.name = new

    @property
    def uniq_id(self, val=''):
        m = hashlib.md5()
        m.update(self.full_name)
        return m.hexdigest()[:8] + val


def build_group_tree_db(db_groups):
    def group_process(f):
        for grp in db_groups:
            # app.logger.info("%s: %s", grp, grp.__dict__)
            yield grp.__dict__.copy()
    return _build_groups_db(GroupTree, None, group_builder=group_process)


def build_group_tree_formdata(formdata):
    def group_process(f):
        for grp in sorted(formdata):
            # app.logger.info("%s: %s", grp, grp.__dict__)
            yield formdata[grp].copy()
    return _build_groups_db(GroupTree, None, group_builder=group_process)


def set_quota_sums(db, root):
    """ Renormalize the sums in the group-tree (@root) of non-leaf nodes """
    for group in root:
        if not group.is_leaf:
            newquota = sum(x.quota for x in group.get_children())

# !! FIXME: and not user_sum_change_auth
            if newquota != group.quota and True:
                app.logger.info("Intermediate group sum %s: %d->%d",
                                group.full_name, group.quota, newquota)
                dbobj = next(x for x in db if x.group_name == group.full_name)
                dbobj.quota = newquota
                group.quota = newquota

            # If newly added group causes a former leaf that has non-zero
            # threshold to become a non-leaf then set it to zero!
            if group.surplus_threshold > 0:
                dbobj = next(x for x in db if x.group_name == group.full_name)
                dbobj.surplus_threshold = 0
