# Copyright 2014 MongoDB Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import email
import rfc822
import re
import imaplib as imap
from email_reply_parser import EmailReplyParser as erp
from datetime import datetime
from base_scraper import BaseScraper

class IMAPScraper(BaseScraper):
    """Scraper that uses IMAP to read email.
       Since it does not use JSON (or even
       raw HTTP) it has a separate implementation
       of the documents() method."""
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self._setup_logger(__name__)
        self.labels = kwargs['labels']
        self.group_re = re.compile(r'^\[(.*)\]\s+(.*)')
        self.subject_re = re.compile(r'([\[\(] *)?(\bRE|FWD?) *([-:;)\]][ :;\])-]*|$)|\]+ *$',
                                     re.IGNORECASE | re.MULTILINE)
        self.header_re = re.compile(".*\(X-GM-THRID (\d+) X-GM-MSGID (\d+)")
        self.message_parts = '(RFC822 X-GM-MSGID X-GM-THRID)'
        self.size = 100

    def login(self):
        user = self.auth[0]
        password = self.auth[1]
        self.imapsrc = imap.IMAP4_SSL('imap.gmail.com', 993)
        self.imapsrc.login(user, password)

    def logout(self):
        self.imapsrc.close()
        self.imapsrc.logout()

    def select(self, label, readonly=True):
        self.imapsrc.select(label, readonly)

    def uid(self, command, *args):
        status, data = self.imapsrc.uid(command, *args)
        if status == 'OK':
            return data
        else:
            print "Status was not OK when running# %s" % command

    def get_message_ids(self):
        if self.last_date:
            last_date = self.last_date.strftime('%d-%b-%Y')
            data = self.uid('search', None, '(SINCE {0})'.format(last_date))
        else:
            data = self.uid('search', None, 'ALL')
        return data[0].split()

    def scrape_label(self, label):
        self.select(label)
        message_ids = self.get_message_ids()
        for num in xrange(0, len(message_ids), self.size):
            messages = self.scrape_messages(message_ids[num:num+self.size])
            for message in messages:
                yield message

    def documents(self):
        self.login()
        for label in self.labels:
            for message in self.scrape_label(label):
                yield [message] # FIXME dirty

    def extract_header(self, header):
        groups = self.header_re.match(header).groups()
        thread_id = groups[0]
        message_id = groups[1]
        return (thread_id, message_id)

    def clean_subject(self, subject):
        subject = self.subject_re.sub('', subject)
        subject = subject.replace('\r\n', '')
        return subject

    def extract_group(self, subject):
        group = None
        group_match = self.group_re.match(subject)

        if group_match is not None:
            group, subject = group_match.groups()

        return group, subject

    def extract_date(self, date):
        timestamp = time.mktime(rfc822.parsedate(date))
        date = datetime.utcfromtimestamp(timestamp)
        return date

    def extract_body(self, message):
        body = None
        for part in message.walk():
            if part.get_content_type() == 'text/plain':
                text = part.get_payload()
                try:
                    body = erp.parse_reply(text)
                except:
                    body = text
        return body

    def scrape_messages(self, message_ids):
        asking_range = str(message_ids[0]) + ':' + str(message_ids[-1])
        self.info("Fetching messages in range [%s]" % asking_range)
        data = self.uid('fetch', asking_range, self.message_parts)
        for headers, message in data[::2]:
            yield self.scrape_message(headers, message)

    def scrape_message(self, headers, message):
        thread_id, message_id = self.extract_header(headers)
        message = email.message_from_string(message)
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
