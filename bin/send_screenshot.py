# -*- coding: utf-8 -*-

import os
import sys
import json
import urllib2
import urlparse
import csv
import re
import gzip
import subprocess
from collections import OrderedDict

from email import Encoders
from email import Utils
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header

import splunk.entity as entity
import splunk.secure_smtplib as secure_smtplib
import splunk.ssl_context as ssl_context
from splunk.util import normalizeBoolean
from splunk.rest import simpleRequest


EMAIL_DELIM = re.compile('\s*[,;]\s*')
CASPER_FOLDER = "casperjs-1.1.4-1"
PHANTOM_FOLDER = "phantomjs-2.1.1-linux-x86_64"
# get current directory
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FILE_NAME = "screenshot"
print >> sys.stderr, "DEBUG Casper: %s, Phantom: %s, Directory: %s" % (CASPER_FOLDER, PHANTOM_FOLDER, DIR_PATH)


def get_alert_actions(sessionKey):
    '''
    Get Settings out of the alert_actions.conf for stanza mail
    '''
    settings = None
    try:
        settings = entity.getEntity('/configs/conf-alert_actions', 'email', sessionKey=sessionKey)
        print >> sys.stderr, "DEBUG alert_actions.conf loaded %s" % settings
    except Exception as e:
        print >> sys.stderr, "ERROR Could not access or parse email stanza of alert_actions.conf. Error=%s" % str(e)

    return settings

def build_email_object(settings):
    '''
    Method to build the email object
    '''
    email = emailBody = MIMEMultipart()
    email['From'] = sender = settings.get('from', 'splunk') 
    email['To'] = "neumann@consist.de"
    email['Subject'] = settings.get('subject', 'Message from Splunk')
    print >> sys.stderr, "DEBUG Email object built From: %s, To: %s, Subject: %s" % (email['To'], email['From'], email['Subject'])
    return email

def build_mime_attachment():
    '''
    Create the MIME attachment
    '''
    # TODO: Change file extensions to variable!
    with open(os.path.join(DIR_PATH, FILE_NAME + ".png"), 'rb') as fp:
        img = MIMEImage(fp.read())
    return img

def send_mail_screenshot(settings, session_key):
    '''
    Setup connection, attach file to mail and send out mail
    '''
    # Get Mail object
    email = build_email_object(settings)

    email.attach(build_mime_attachment())
    
    sender     = email['From']
    use_ssl    = normalizeBoolean(settings.get('.use_ssl', False))
    use_tls    = normalizeBoolean(settings.get('use_tls', False))
    server     = settings.get('mailserver', 'localhost')

    username   = settings.get('auth_username', '')
    password   = settings.get('clear_password', '')
    recipients = []

    if email['To']:
        recipients.extend(EMAIL_DELIM.split(email['To']))

    # Clear leading / trailing whitespace from recipients
    recipients = [r.strip() for r in recipients]

    mail_log_msg = 'Sending email. subject="%s", recipients="%s", server="%s"' % (
        email['subject'],
        str(recipients),
        str(server)
    )

    try:
        # make sure the sender is a valid email address
        if sender.find("@") == -1:
            sender = sender + '@' + socket.gethostname()
            if sender.endswith("@"):
              sender = sender + 'localhost'

        # setup the Open SSL Context
        sslHelper = ssl_context.SSLHelper()
        serverConfJSON = sslHelper.getServerSettings(session_key)
        # Pass in settings from alert_actions.conf into context
        ctx = sslHelper.createSSLContextFromSettings(
            sslConfJSON=settings,
            serverConfJSON=serverConfJSON,
            isClientContext=True)

        # send the mail
        if not use_ssl:
            smtp = secure_smtplib.SecureSMTP(host=server)
        else:
            smtp = secure_smtplib.SecureSMTP_SSL(host=server, sslContext=ctx)

        # smtp.set_debuglevel(1)

        if use_tls:
            smtp.starttls(ctx)
        if len(username) > 0 and password is not None and len(password) >0:
            smtp.login(username, password)

        smtp.sendmail(sender, recipients, email.as_string())
        smtp.quit()

    except Exception, e:
        print >> sys.stderr, "ERROR Sending mail unsuccessful: %s / %s" % (mail_log_msg, e)
        return False
    
    return True
    

def expand_system_path_variable ():
    '''
    Expand the System Path variable with phantom js path, so it can be found by casperjs
    '''
    os.environ['PATH'] = os.environ['PATH'] + ":" + os.path.join(DIR_PATH, PHANTOM_FOLDER, "bin")
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
    try:
        subprocess.call([os.path.join(DIR_PATH, CASPER_FOLDER, "bin", "casperjs"), os.path.join(DIR_PATH, "screenshot.js"), dashboard_url, "15", FILE_NAME, session_key, "admin"])
        return True
    except Exception, e:
        print >> sys.stderr, "ERROR Cannot create Screenshot: %s" % e
        return False

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
        alert_actions_settings = get_alert_actions(session_key)
        if not send_mail_screenshot(alert_actions_settings, session_key):
            sys.exit(3)
    except Exception, e:
        print >> sys.stderr, "ERROR Unexpected error: %s" % e
        sys.exit(4)
