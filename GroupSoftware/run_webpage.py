#!/usr/bin/python
import sys

if len(sys.argv) > 1 and sys.argv[1] == "init":
    import gqweb.db
    gqweb.db.init_db()
else:
    from gqweb import app
    app.run(debug=True, host='0.0.0.0', threaded=True)
