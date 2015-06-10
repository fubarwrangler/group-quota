# *****************************************************************************

# from gqweb import app

from group.group import AbstractGroup
# from group.db import _build_groups_db
# from flask import request

import sys

from sqlalchemy import Table, orm

from database import Base


class Group(Base):
    __table__ = Table('atlas_group_quotas', Base.metadata, autoload=True)

    @orm.reconstructor
    def on_load(self):
        AbstractGroup.__init__(self, self.group_name.split('.')[-1])
