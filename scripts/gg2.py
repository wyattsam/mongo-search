#!/usr/bin/env python
import email
import rfc822
import time
import re
import sys
import imaplib as imap
from datetime import datetime
from email_reply_parser import EmailReplyParser as erp
from pymongo import MongoClient

MONGO = MongoClient('localhost:27017')
DB = MONGO['xgen']

if len(sys.argv) == 5:
    DB.authenticate(sys.argv[3], sys.argv[4])

GOOGLE = DB['google_groups']
COMBINED = DB['combined']
SCRAPES = DB['scrapes']

# user provided login credentials
credentials = None
if len(sys.argv) >= 3:
    gmail_user, gmail_pass = sys.argv[1:3]
    credentials = (gmail_user, gmail_pass)
else:
    raise ValueError("Must supply gmail username and password")

USER, PASSWORD = credentials

MAIL = imap.IMAP4_SSL('imap.gmail.com', 993)
MAIL.login(USER, PASSWORD)

header_re = re.compile(".*\(X-GM-THRID (\d+) X-GM-MSGID (\d+)")
sub_re = re.compile(r'([\[\(] *)?(\bRE|FWD?) *([-:;)\]][ :;\])-]*|$)|\]+ *$',
                    re.IGNORECASE | re.MULTILINE)
group_re = re.compile(r'^\[(.*)\]\s+(.*)')

def save_message(msgnum):
    status, data = MAIL.uid('fetch', msgnum, '(RFC822 X-GM-MSGID X-GM-THRID)')
    if status == 'OK':
        gm_headers = data[0][0]
        groups = header_re.match(gm_headers).groups()
        message = email.message_from_string(data[0][1])

        date = datetime.utcfromtimestamp(
            time.mktime(rfc822.parsedate(message['Date']))
        )
        thread_id = groups[0]
        message_id = groups[1]

        group = None
        subject = sub_re.sub('', message['Subject'])
        group_match = group_re.match(subject)
        if group_match is not None:
            group, subject = group_match.groups()

        msgdoc = {
            '_id': 'gg-%s' % message_id,
            'date': date,
            'subject': subject,
            'group': group,
            'sender': message['X-Original-Sender'],
            'from': message['From'],
            'gm_thread_id': int(thread_id),
            'gm_message_id': int(message_id),
            'gg_message_id': message['Message-Id']
        }

        for part in message.walk():
            if part.get_content_type() == 'text/plain':
                text = part.get_payload()
                try:
                    msgdoc['body'] = erp.parse_reply(text)
                except:
                    msgdoc['body'] = text
                    print "Error parsing reply in message#: %s" % message_id

                GOOGLE.save(msgdoc)
                msgdoc['source'] = 'google_groups'
                COMBINED.save(msgdoc)
    else:
        print "Status was not OK when fetching message# %s" % msgnum


def save_group(group):
    print '[GROUP] %s' % group
    MAIL.select(group, True)
    status, data = MAIL.uid('search', None, 'ALL')

    for msgnum in data[0].split():
        save_message(msgnum)

if __name__ == '__main__':
    scrape = SCRAPES.insert({
        'source': 'google_groups',
        'start': datetime.now(),
        'state': 'running'
    })

    try:
        save_group('freesupport')

        SCRAPES.update({'_id': scrape},
            {'$set': {'state': 'complete', 'end': datetime.utcnow()}})

    except Exception as error:
        SCRAPES.update({'_id': scrape},
            {'$set': {'state': 'failed', 'error': str(error)}})

MAIL.logout()
MAIL.close()
