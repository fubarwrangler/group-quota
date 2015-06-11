# *****************************************************************************

from group.group import AbstractGroup
from group.db import _build_groups_db

from sqlalchemy import Table

from database import Base


class Group(Base):
    __table__ = Table('atlas_group_quotas', Base.metadata, autoload=True)


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


def build_group_tree(db_groups):
    def group_process(f):
        for grp in db_groups:
            yield grp.__dict__
    return _build_groups_db(GroupTree, None, group_builder=group_process)
