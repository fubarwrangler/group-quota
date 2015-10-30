# ===========================================================================
# Database models for BNL T3 pool users and institutes
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relation as relationship

from . import Base


class T3User(Base):
    __tablename__ = 't3users'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    name = Column(String(32), nullable=False, primary_key=True)
    affiliation = Column(String(32),
                         ForeignKey('institutes.name',
                                    ondelete='restrict', onupdate='cascade'),
                         nullable=False, primary_key=True)
    fullname = Column(String(256))

    institute = relationship('T3Institute', uselist=False)


class T3Institute(Base):
    __tablename__ = 'institutes'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    name = Column(String(32), nullable=False, primary_key=True)
    group = Column(String(128), ForeignKey('groups.group_name', onupdate='cascade'))
    fullname = Column(String(256))

    users = relationship('T3User')
