from base_scraper import BaseScraper
from time import sleep
import requests

class GithubScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self.orgurl = 'https://api.github.com/orgs/'
        self.orgs = kwargs['orgs']
        self.org = self.orgs.pop(0)
        self.repos = []
        self.repo = {}

        self.needs_setup = True

        params = {'per_page': 100}
        if self.auth:
            self.params = dict([self.auth])
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
            return # TODO should throw a custom exception
        self.apiurl = self.repo['url'] + "/commits"
        self.info("Starting repo %s" % self.repo['full_name'])

    def _scrape(self, doc, links=None):
        for commit in doc:
            if 'message' not in commit:
                commit['_id'] = self.repo['full_name'] + '-' + commit['sha']
                commit['repo'] = {
                    'full_name': self.repo['full_name'],
                    'name': self.repo['name'],
                    'url': self.repo['url']
                }
                commit['subsource'] = self.repo['name']
                commit['org'] = self.org
                yield commit
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
                    # TODO
                    pass
            else:
                self.repo = self.repos.pop(0)
                self.apiurl = self.repo['url'] + "/commits"
                self.info("Starting repo %s" % self.repo['full_name'])
