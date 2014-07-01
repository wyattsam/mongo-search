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
import requests

class DocsScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self._setup_logger(__name__)
        kinds = kwargs['kinds']
        self.apiurl = "http://docs.mongodb.org/"
        self.kinds = kinds
        self.kind = ''
        self.urlexts = []

        self.needs_setup = True

    def _scrape(self, doc, links=None):
        ret = None
        if 'text' in doc:
            pname = doc['current_page_name']
            _id = '-'.join([self.name, self.kind, pname])
            doc['_id'] = _id
            doc['section'] = self.kind
            doc['subsource'] = self.kind
            ret = doc
        else:
            self.err("Received unexpected message %s" % str(doc))
            self.finished = True

        # ensure we advance
        if len(self.urlexts) > 0:
            url = self.urlexts.pop(0)
            self.kind = url[0]
            self.apiurl = url[1]
        else:
            self.finished = True
        yield ret

    def _setup(self):
        # TODO: can the self.loading stuff be taken care of with a decorator?
        for k in self.kinds:
            urls = requests.get(self.apiurl + '/' + k + '/json/.file_list').text.split('\n')
            self.urlexts.extend([(k,u) for u in urls])
        # make sure apiurl is updated
        url = self.urlexts.pop(0)
        self.kind = url[0]
        self.apiurl = url[1]
