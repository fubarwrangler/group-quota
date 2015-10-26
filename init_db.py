#!/usr/bin/python

import gqweb.db
print "Connected to: %s" % gqweb.db.app.config['DATABASE_URI']
gqweb.db.init_db()
