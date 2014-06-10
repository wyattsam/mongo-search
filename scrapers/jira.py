from base_scraper import BaseScraper
from time import sleep
import requests

class JiraScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self.skip = kwargs['skip']
        self.apiurl = 'https://jira.mongodb.org/rest/api/2/search/'
        self.pkeys = []
        self.needs_setup = True
        self.limit = 100
        self.params = {
            'startAt': 0,
            'maxResults': self.limit,
            'fields': 'key,summary,description,comment,status'
        }
        self.project = ""

    def _setup(self):
        projects = requests.get(url='https://jira.mongodb.org/rest/api/2/project/', auth=self.auth, verify=False).json(strict=False)
        self.pkeys = [p['key'] for p in projects if p not in self.skip]
        self.project = self.pkeys.pop(0)
        self.params['jql'] = 'PROJECT={project} order by KEY asc'.format(project=self.project)
        self.info("Searching projects %s" % self.pkeys)

    def _scrape(self, doc):
        issues = None # why do i have to do this?
        if 'issues' in doc:
            issues = doc['issues']
            if issues:
                for issue in issues:
                    issue['_id'] = issue['key']
                    issue['subsource'] = self.project
                    issue['fields']['status'] = issue['fields']['status']['name']
                    yield issue
            else:
                self.debug("'issues' was None in result document")
        else:
            self.info("'issues' was not present in result document")
            self.finished = True

        if issues and len(issues) >= self.limit: # we got as many as we could; this means there are more issues
            self.params['startAt'] += len(issues)
            sleep(1)
        else: # we exhausted this project, time to move on
            if len(self.pkeys) == 0:
                self.debug("no more projects to scrape")
                self.finished = True
            else:
                self.project = self.pkeys.pop(0)
                self.params['jql'] = 'PROJECT={project} order by KEY asc'.format(project=self.project)
