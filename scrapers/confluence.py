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

from base_scraper import BaseScraper
from HTMLParser import HTMLParser
import re
import requests

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

class ConfluenceScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self._setup_logger(__name__)
        self.spaces = kwargs['spaces']
        self.needs_setup = True
        self.base_url = "https://wiki.mongodb.com/rest/prototype/1/"
        self.page = 0
        self.page_ids = []
        self.page_id = -1

    def strip_tags(self, html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()

    def update_params(self):
        self.params = {
            'type': 'page',
            'spaceKey': self.space,
            'startIndex': self.page
        }

    def advance_space(self):
        req_url = ''.join([self.base_url, 'search.json'])
        self.space = self.spaces.pop(0)
        self.update_params()
        results = requests.get(req_url, params=self.params, auth=self.auth).json(strict=False)
        self.size = results['totalSize']
        while True:
            res = results['result']
            extended = None
            if res:
                extended = [elem['id'] for elem in res]
                self.page_ids.extend(extended)
            if not extended:
                break

            self.page += 50
            if self.page > self.size:
                break
            self.update_params()
            self.debug("getting page starting at %s for space %s" % (self.page, self.space))
            results = requests.get(req_url, params=self.params, auth=self.auth).json(strict=False)
        self.advance_page()
        self.page = 0

    def advance_page(self):
        self.page_id = self.page_ids.pop(0)
        self.apiurl = ''.join([self.base_url, 'content/', str(self.page_id), '.json'])

    def _setup(self):
        self.advance_space()

    def _scrape(self, doc, links=None):
        html_body = doc['body']['value']
        if '{wiki}' in html_body:
            r = re.compile(r'\{wiki\}(.*)\{wiki\}', re.MULTILINE | re.DOTALL)
            result = r.search(html_body)
            if result:
                html_body = result.group(1)

        text_body = self.strip_tags(html_body)
        yield {
            '_id': doc['id'],
            'title': doc['title'],
            'body': text_body,
            'url': doc['link'][0]['href'],
            'space': self.space,
            'subsource': self.space
        }

        if len(self.page_ids) > 0:
            self.advance_page()
        else: # we are out of pages
            if len(self.spaces) == 0: # we are also out of spaces
                self.finished = True
            else:
                self.advance_space()
                self.page = 0
