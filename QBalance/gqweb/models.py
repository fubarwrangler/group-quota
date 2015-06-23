# ===========================================================================
# Database model and tree-object with HTML hooks from group-class and info
# about field-types and validation methods used for form data
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
import re

from group.group import AbstractGroup
from group.db import _build_groups_db

from . import app

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

    def rename(self, new):
        self.name = new


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

# *****************************************************************************
# The following is all for form validation of the user-input data
# *****************************************************************************

name_validate = lambda name: bool(re.match(r'^group_[a-z0-9_\.]+$', name))
new_name_validate = lambda name: bool(re.match(r'^[a-z0-9_]+$', name))
positive_int = lambda x: x > 0.0
non_zero_int = lambda x: x > 1
non_negative = lambda x: x >= 0.0

type_map = {
    'priority': (float, positive_int, 'floating point value greater than zero'),
    'weight': (float, non_negative, 'non-negative floating point value'),
    'quota': (int, non_zero_int, 'integer greater than 0'),
    'new_name': (str, new_name_validate, 'string matching [a-z_]+'),
    'group_name': (str, name_validate, 'string matching [a-z_](.[a-z_])*'),
    'surplus_threshold': (int, non_negative, 'integer >= 0'),
    'accept_surplus': (lambda x: x == 'on', lambda x: True, 'boolean'),
}
