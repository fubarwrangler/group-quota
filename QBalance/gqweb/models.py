# *****************************************************************************
import re

from group.group import AbstractGroup
from group.db import _build_groups_db

from gqweb import app

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


def name_validate(name):
    return re.match(r'^[a-z_\.]+$', name) and len([x for x in name.split('.') if x]) > 0

type_map = {
    'priority': (float, lambda x: x > 0.0, 'floating point value greater than zero'),
    'weight': (float, lambda x: x >= 0.0, 'non-negative floating point value'),
    'quota': (int, lambda x: x > 1, 'integer greater than 0'),
    'group_name': (str, name_validate, 'string matching [a-z_].[a-z_]+'),
    'surplus_threshold': (int, lambda x: x >= 0, 'integer >= 0'),
    'accept_surplus': (lambda x: x == 'on', lambda x: True, 'boolean'),
}


def build_group_tree_db(db_groups):
    def group_process(f):
        for grp in db_groups:
            # app.logger.info("%s: %s", grp, grp.__dict__)
            yield grp.__dict__.copy()
    return _build_groups_db(GroupTree, None, group_builder=group_process)
