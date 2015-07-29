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

from sqlalchemy import (Table, Column, Integer, String, Boolean, Float, func,
                        ForeignKey, TIMESTAMP)
from . import Base

group_id = "{0}.id".format(app.config['TABLE_NAME'])


class Group(Base):
    __tablename__ = app.config['TABLE_NAME']
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    group_name = Column(String(128), nullable=False, unique=True)
    quota = Column(Integer, nullable=False, server_default='0')
    priority = Column(Float, nullable=False, server_default='10.0')
    weight = Column(Float, nullable=False, server_default='1.0')
    accept_surplus = Column(Boolean, nullable=False, server_default='0')
    busy = Column(Integer, nullable=False, server_default='0')
    surplus_threshold = Column(Integer, nullable=False, server_default='0')
    last_update = Column(TIMESTAMP, nullable=False, server_default=func.now())
    last_surplus_update = Column(TIMESTAMP, nullable=True)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    active = Column(Boolean, default=False)


class Role(Base):
    __tablename__ = 'roles'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)


class UsageLog(Base):
    """ Not used by web-interface, but let us create it anyway ! """

    __tablename__ = 'atlas_queue_log'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, ForeignKey(group_id, ondelete="cascade"), primary_key=True)
    amount_in_queue = Column(Integer, nullable=False, server_default='0')
    query_time = Column(TIMESTAMP, nullable=False, index=True,
                        server_default=func.now())

user_role_table = Table('user_roles', Base.metadata,
                        Column('user_id', Integer, ForeignKey('users.id')),
                        Column('role_id', Integer, ForeignKey('roles.id'))
                        )


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
