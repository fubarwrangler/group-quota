from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from group.group import AbstractGroup


SQLALCHEMY_DATABASE_URI = 'mysql://willsk@localhost/group_quotas'

engine = create_engine(SQLALCHEMY_DATABASE_URI, convert_unicode=True, echo=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base(cls=AbstractGroup)
Base.metadata = MetaData(bind=engine)
Base.query = db_session.query_property()


def cooperative_constructor(cls):
    initmeth = cls.__init__

    def _concrete_init(self, **kwargs):
        # enable cooperative inheritance
        super(cls, self).__init__()
        # pass through to original constructor
        initmeth(self, **kwargs)
    return _concrete_init

Base.__init__ = cooperative_constructor(Base)
