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
from bs4 import BeautifulSoup
import json
import requests
import ssl

class GenericScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self._setup_logger(__name__)
        self.url_targets = kwargs['url_targets']
        self.base_url = kwargs['url']
        self.url_ext, self.target = self.url_targets.pop(0)
        self.apiurl = self.base_url + self.url_ext

    def documents(self):
        while True:
            try:
               response = requests.get(self.apiurl, params=self.params,
                                       auth=self.auth, verify=False,
                                       timeout=60)
            except requests.exceptions.SSLError:
                self.warn("Experienced requests.exceptions.SSLError timeout; continuing")
                continue
            except ssl.SSLError:
                self.warn("Experienced ssl.SSLError timeout; continuing")
                continue
            yield self._scrape(response.text, response.links)
            if len(self.url_targets) > 0:
                self.url_ext, self.target = self.url_targets.pop(0)
                self.apiurl = self.base_url + self.url_ext
            else:
                break

    def _scrape(self, doc, links=None):
        soup = BeautifulSoup(doc)
        text = soup.find(id=self.target).get_text()
        title = soup.title.text or self.apiurl
        yield {
            '_id': self.name + '-' + self.url_ext + '-' + self.target,
            'url': self.apiurl,
            'title': title,
            'subsource': self.url_ext if len(self.url_ext) > 0 else None,
            'section': self.target,
            'text': text
        }
