#!/usr/bin/python


import os.path, sys
import cgitb

cgitb.enable()
os.environ['SCRIPT_NAME'] = os.path.basename(sys.argv[0])

if __name__ == "__main__":

    import main

    main.do_main("atlas.cfg")
