# -*- coding: utf-8 -*-

import os
import sys
import json
import urllib2
import urlparse
import csv
import gzip
import subprocess
from collections import OrderedDict

casper_folder = "casperjs-1.1.4-1"
phantom_folder = "phantomjs-2.1.1-linux-x86_64"
# get current directory
dir_path = os.path.dirname(os.path.realpath(__file__))
print >> sys.stderr, "DEBUG Casper: %s, Phantom: %s, Directory: %s" % (casper_folder, phantom_folder, dir_path)


def expand_system_path_variable ():
    '''
    Expand the System Path variable with phantom js path, so it can be found by casperjs
    '''
    os.environ['PATH'] = os.environ['PATH'] + ":" + os.path.join(dir_path, phantom_folder, "bin")
    print >> sys.stderr, "DEBUG Environment PATH with PhantomJS: %s" % os.environ['PATH']

def get_server_uri (results_link):
    '''
    Get Name of server out of the result field of the given payload
    '''
    server_uri = urlparse.urlsplit(results_link).scheme + "://" + urlparse.urlsplit(results_link).netloc
    print >> sys.stderr, "DEBUG Splunk Server URI: %s" % server_uri
    return server_uri

def build_dashboard_url (server_uri, dashboard, app) :
    '''
    Build the URL to the dashboard
    '''
    dashboard_url = server_uri + "/app/" + app +"/" + dashboard
    print >> sys.stderr, "DEBUG dashboard url: %s" % server_uri
    return dashboard_url

def create_screenshot_dashboard(dashboard_url, session_key):
    expand_system_path_variable()
    print >> sys.stderr, "DEBUG Call casperjs for screenshot"   
    # run casperjs
    subprocess.call([os.path.join(dir_path, casper_folder, "bin", "casperjs"), os.path.join(dir_path, "screenshot.js"), dashboard_url, "15", "test", session_key, "admin"])

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "--execute":
        print >> sys.stderr, "FATAL Unsupported execution mode (expected --execute flag)"
        sys.exit(1)
    try:
        payload = json.loads(sys.stdin.read())
        print >> sys.stderr, "DEBUG payload from Splunk in JSON format: %s" % payload
        server_uri = get_server_uri(payload.get('results_link'))
        session_key = payload.get('session_key')
        dashboard = payload['configuration'].get('dashboard')
        app = payload['configuration'].get('app')
        print >> sys.stderr, "DEBUG Dashboard name: %s, App name: %s, Session_Key: %s" % (dashboard, app, session_key)
        dashboard_url = build_dashboard_url(server_uri, dashboard, app)
        if not create_screenshot_dashboard(dashboard_url, session_key):
            sys.exit(2)
        # TODO: send mail with screenshot
    except Exception, e:
        print >> sys.stderr, "ERROR Unexpected error: %s" % e
        sys.exit(3)
