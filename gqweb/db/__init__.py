# ===========================================================================
# Simple DB-Setup boilerplate
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from ..application import app, BNLT3

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine(app.config['DATABASE_URI'],
                       echo=app.config['DB_ECHO'],
                       convert_unicode=True,
                       pool_recycle=app.config['DBPOOL_RECYCLE'])

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.metadata = MetaData(bind=engine)
Base.query = db_session.query_property()


def init_db():
    import models  # flake8: noqa -- to register models
    if BNLT3:
        import t3models  # flake8: noqa -- to register models
    Base.metadata.create_all(bind=engine)
