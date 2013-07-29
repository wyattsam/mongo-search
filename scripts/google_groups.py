import time
import email
import rfc822
import re
import imaplib as imap
from email_reply_parser import EmailReplyParser as erp
from datetime import datetime
from scrapers import Scraper


class GoogleGroupsScraper(Scraper):
    NAME = 'google_groups'
    HEADER_RE = re.compile(".*\(X-GM-THRID (\d+) X-GM-MSGID (\d+)")
    SUBJECT_RE = re.compile(r'([\[\(] *)?(\bRE|FWD?) *([-:;)\]][ :;\])-]*|$)|\]+ *$',
                            re.IGNORECASE | re.MULTILINE)
    GROUP_RE = re.compile(r'^\[(.*)\]\s+(.*)')
    MESSAGE_PARTS = '(RFC822 X-GM-MSGID X-GM-THRID)'

    def __init__(self, labels, credentials):
        self.credentials = credentials
        self.labels = labels

    def login(self):
        user = self.credentials['user']
        password = self.credentials['password']
        self.gmail = imap.IMAP4_SSL('imap.gmail.com', 993)
        self.gmail.login(user, password)

    def logout(self):
        self.gmail.close()
        self.gmail.logout()

    def select(self, label, readonly=True):
        self.gmail.select(label, readonly)

    def uid(self, command, *args):
        status, data = self.gmail.uid(command, *args)
        if status == 'OK':
            return data
        else:
            print "Status was not OK when running# %s" % command

    def get_message_ids(self):
        data = self.uid('search', None, 'ALL')
        return data[0].split()

    def scrape_label(self, label):
        print '[label] %s' % label
        self.select(label)
        for message_id in self.get_message_ids():
            yield self.scrape_message(message_id)

    def scrape(self):
        self.login()
        for label in self.labels:
            for message in self.scrape_label(label):
                yield message

    def extract_header(self, header):
        groups = self.HEADER_RE.match(header).groups()
        thread_id = groups[0]
        message_id = groups[1]
        return (thread_id, message_id)

    def clean_subject(self, subject):
        subject = self.SUBJECT_RE.sub('', subject)
        return subject

    def extract_group(self, subject):
        group = None
        group_match = self.GROUP_RE.match(subject)

        if group_match is not None:
            group, subject = group_match.groups()

        return group, subject

    def extract_date(self, date):
        timestamp = time.mktime(rfc822.parsedate(date))
        date = datetime.utcfromtimestamp(timestamp)
        return date

    def extract_body(self, message):
        for part in message.walk():
            if part.get_content_type() == 'text/plain':
                body = None
                text = part.get_payload()
                try:
                    body = erp.parse_reply(text)
                except:
                    body = text
        return body

    def scrape_message(self, message_id):
        data = self.uid('fetch', message_id, self.MESSAGE_PARTS)
        headers = data[0][0]
        thread_id, message_id = self.extract_header(headers)
        message = email.message_from_string(data[0][1])
        subject = self.clean_subject(message['Subject'])
        group, subject = self.extract_group(subject)
        date = self.extract_date(message['Date'])
        body = self.extract_body(message)
        gg_id = message['Message-Id'].strip('<>')

        msgdoc = {
            '_id': 'gg-%s' % message_id,
            'date': date,
            'subject': subject,
            'group': group,
            'sender': message['X-Original-Sender'],
            'from': message['From'],
            'thread_id': int(thread_id),
            'message_id': int(message_id),
            'google_groups_id': gg_id,
            'body': body
        }

        return msgdoc
