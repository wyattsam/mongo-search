from time import sleep
from scrapers import JSONScraper


class JiraScraper(JSONScraper):
    NAME = 'jira'
    API_BASE = 'https://jira.mongodb.org/rest/api/2/'
    SEARCH_URL = API_BASE + 'search/'
    PROJECT_URL = API_BASE + 'project/'
    PAGE_SIZE = 100

    def __init__(self, credentials=None, skip=[]):
        self.skip = skip
        self.credentials = credentials

    def get_projects(self):
        projects = self.get_json(url=self.PROJECT_URL, auth=self.credentials)
        project_keys = [project['key'] for project in projects]
        return project_keys

    def search_issues(self, jql):
        return self.get_json(self.SEARCH_URL, jql, auth=self.credentials)

    def scrape_issue(self, issue, project):
        issue['_id'] = issue['key']
        issue['project'] = project
        issue['subsource'] = project
        issue['fields']['status'] = issue['fields']['status']['name']
        return issue

    def scrape_issues(self, project):
        jql = 'PROJECT={project} order by KEY asc'.format(project=project)
        params = {
            'jql': jql,
            'startAt': 0,
            'maxResults': self.PAGE_SIZE,
            'fields': 'key,summary,description,comment,status',
            'expand': 'changelog'
        }

        while True:
            result = self.search_issues(params)
            if 'issues' in result:
                issues = result['issues']
                if issues:
                    for issue in issues:
                        yield self.scrape_issue(issue, project)
                else:
                    break
            else:
                break

            params['startAt'] += len(issues)
            sleep(1)

    def scrape_project(self, project):
        if project not in self.skip:
            print "[PROJECT] " + project
            for issue in self.scrape_issues(project):
                yield issue

    def scrape(self):
        projects = self.get_projects()
        print '[JIRA] %s' % projects
        for project in projects:
            for issue in self.scrape_project(project):
                yield issue


if __name__ == '__main__':
    import settings
    from scrapers import ScrapeRunner
    runner = ScrapeRunner(**settings.MONGO)
    scraper = JiraScraper(**settings.JIRA)
    runner.run(scraper)
