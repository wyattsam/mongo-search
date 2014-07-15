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

class GithubScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self._setup_logger(__name__)
        self.orgurl = 'https://api.github.com/orgs/'
        self.orgs = kwargs['orgs']
        self.org = self.orgs.pop(0)
        self.repos = []
        self.repo = {}

        self.needs_setup = True

        params = {'per_page': 100}
        if self.auth:
            self.params = {
                'client_id': self.auth[0],
                'client_secret': self.auth[1]
            }
            self.params.update(**params)
        else:
            self.params = params
        self.auth = None

    def _setup(self):
        url = self.orgurl + self.org + "/repos"
        self.repos = requests.get(url, params=self.params).json(strict=False)
        try:
            self.repo = self.repos.pop(0)
        except KeyError:
            self.err(self.repos['message'])
            raise StopIteration()
        self.apiurl = self.repo['url'] + "/commits"
        self.info("Starting repo %s" % self.repo['full_name'])

    def _scrape(self, doc, links=None):
        for commit in doc:
            if 'message' not in commit:
                try:
                    commit['_id'] = self.repo['full_name'] + '-' + commit['sha']
                    commit['repo'] = {
                        'full_name': self.repo['full_name'],
                        'name': self.repo['name'],
                        'url': self.repo['url']
                    }
                    commit['subsource'] = self.repo['name']
                    commit['org'] = self.org
                    yield commit
                except Exception: # we get a differently typed message when github shuts us off
                    self.error("GitHub returned an error document: %s" % doc)
                    raise StopIteration()
        if 'next' in links:
            self.info("Getting next page of repo %s" % self.repo['name'])
            self.apiurl = links['next']['url']
            sleep(1)
        else:
            #if we have no more repos, try a new org
            if len(self.repos) == 0:
                if len(self.orgs) == 0:
                    self.finished = True
                else:
                    # TODO switch to new org
                    pass
            else:
                self.repo = self.repos.pop(0)
                self.apiurl = self.repo['url'] + "/commits"
                self.info("Starting repo %s" % self.repo['full_name'])
