import sys
import json
import urllib2
import csv
import gzip
from collections import OrderedDict


def send_dashboard(session_key, dashboard, app):
    return True   


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "--execute":
        print >> sys.stderr, "FATAL Unsupported execution mode (expected --execute flag)"
        sys.exit(1)
    try:
        settings = json.loads(sys.stdin.read()) 
        session_key = settings.get('session_key')
        dashboard = settings['configuration'].get('dashboard')
        app = settings['configuration'].get('app')
        print >> sys.stderr, "Key: %s, Dashboard: %s, App: %s" % (session_key, dashboard, app)    
        if not send_dashboard(session_key, dashboard, app):
            sys.exit(2)
    except Exception, e:
        print >> sys.stderr, "ERROR Unexpected error: %s" % e
        sys.exit(3)
