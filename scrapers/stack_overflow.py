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

from time import sleep, mktime
from base_scraper import BaseScraper

class StackOverflowScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self._setup_logger(__name__)
        self.apiurl = "https://api.stackexchange.com/2.1/search"
        self.tags = kwargs['tags']
        self.tag = 0
        self.params = {
            'site': 'stackoverflow',
            'tagged': self.tags[self.tag],
            'filter': '!*1Klotvkqr2dciMbX*Qdafx4aenCPiyZAdUE1x(1w',
            'page': 1,
            'order': 'asc',
            'pagesize': 100
        }
        if self.last_date:
            date = int(mktime(self.last_date.timetuple()))
            self.params.update({
                'sort': 'activity',
                'min': date,
            })
        else:
            self.params.update({
                'sort': 'creation'
            })

    def _scrape(self, doc, links=None):
        self.info('[%s] page %s' % (self.params['tagged'], self.params['page']))
        items = doc.get('items', [])
        if items:
            for item in items:
                key = self.name + "-" + str(item['question_id'])
                item['_id'] = key
                yield item

            # this tag is empty
            if not doc['has_more']:
                # check for more tags
                if len(self.tags) > self.tag+1:
                    self.tag += 1
                    self.params['tagged'] = self.tags[self.tag]
                    self.params['page'] = 1
                # no more tags, bow out
                else:
                    self.finished = True
            # keep going on this tag
            else:
                self.params['page'] += 1
        else:
            self.finished = True

        if 'backoff' in doc:
            backoff = doc['backoff']
            self.warn('backing off from stackoverflow for %s seconds' % backoff)
            sleep(backoff)
