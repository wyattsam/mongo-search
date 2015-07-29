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

class ProfilesScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self._setup_logger(__name__)
        self.apiurl = 'https://corp.mongodb.com/api/employee'
        self.params = {'expand': 'team'}

    def _scrape(self, doc, links=None):
        try:
            for d in doc['employees']:
                eid = d['uri'].partition("/api/employee/")[2]
                d['crowd_id'] = eid
                d['_id'] = 'employee-' + eid
                d['full_name'] = " ".join([d['first_name'], d['last_name']])
                yield d
        except TypeError:
            # Temporary code that will catch an intermittent type error that
            # happens every once in a while.  This should be removed in a
            # later commit
            print "Caught the elusive profiles TypeError!  Here is what doc is:"
            print doc
        self.finished = True # one query for everyone; wow!
