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
from time import sleep
import requests

class JiraScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self._setup_logger(__name__)
        self.skip = kwargs['skip']
        self.apiurl = 'https://jira.mongodb.org/rest/api/2/search/'
        self.pkeys = []
        self.needs_setup = True
        self.limit = 100
        self.total = 0
        self.processed = 0
        self.params = {
            'startAt': 0,
            'maxResults': self.limit,
            'fields': 'key,summary,description,comment,status'
        }
        self.project = ""

    def _setup(self):
        projects = requests.get(url='https://jira.mongodb.org/rest/api/2/project/', auth=self.auth, verify=False).json(strict=False)
        self.pkeys = [p['key'] for p in projects if p['key'] not in self.skip]
        self.project = self.pkeys.pop(0)
        self.set_jql()
        self.debug("Searching projects %s" % self.pkeys)
        self.info("Beginning project %s" % self.project)

    def set_jql(self):
        if self.last_date:
            last_date = self.last_date.strftime('%Y/%m/%d %H:%M')
            print 'looking for things after', last_date
            self.params['jql'] = 'PROJECT={project} and updated>"{date}" order by KEY asc'.format(
                    project=self.project,
                    date=last_date
                    )
        else:
            self.params['jql'] = 'PROJECT={project} order by KEY asc'.format(project=self.project)

    def _scrape(self, doc, links=None):
        issues = None
        if 'issues' in doc and 'total' in doc:
            issues = doc['issues']
            self.total = doc['total']
            if issues:
                for issue in issues:
                    issue['_id'] = issue['key']
                    issue['subsource'] = self.project
                    issue['fields']['status'] = issue['fields']['status']['name']
                    yield issue
                self.processed += len(issues)
            else:
                self.info("'issues' was None in result document on project %s" % self.project)
        else:
            self.info("'issues' was not present in result document")

        if self.processed < self.total: # there are more issues
            self.params['startAt'] += len(issues)
            sleep(1) # don't dos jira
        else: # we exhausted this project, time to move on
            if len(self.pkeys) == 0:
                self.info("no more projects to scrape")
                self.finished = True
            else:
                self.project = self.pkeys.pop(0)
                self.info("Beginning project: %s" % self.project)
                self.set_jql()
                self.params['startAt'] = 0
                self.total = 0
                self.processed = 0
