# *****************************************************************************

from sqlalchemy import Table

from database import Base


class Group(Base):
    __table__ = Table('atlas_group_quotas', Base.metadata, autoload=True)
