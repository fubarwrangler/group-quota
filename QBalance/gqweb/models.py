# *****************************************************************************

from gqweb import app

from group.group import AbstractGroup

# from flask import request


from sqlalchemy import create_engine, Table
from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.sql import select, cast
# from sqlalchemy import func


engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'],
                       echo=app.config.get('SQLALCHEMY_ECHO', True))

# engine = create_engine('mysql://willsk@localhost/group_quotas', echo=True)

Base = declarative_base(engine)


class Group(AbstractGroup, Base):
    __table__ = Table('atlas_group_quotas', Base.metadata,
                      autoload=True)
