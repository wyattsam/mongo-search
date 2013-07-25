import requests
from scrapers import JSONScraper


class GitHubScraper(JSONScraper):
    NAME = 'github'
    API_BASE = 'https://api.github.com/'
    ORGS_URL = API_BASE + 'orgs/'
    PER_PAGE = 100

    def __init__(self, credentials=None, organizations=[]):
        self.credentials = credentials
        self.organizations = organizations

    def commit_params(self):
        return dict(self.credentials, per_page=self.PER_PAGE)

    def get_repos(self, organization):
        url = self.ORGS_URL + organization + '/repos'
        repos = self.get_json(url, self.credentials)
        return repos

    def scrape_commit(self, repo, commit):
        commit['repo'] = {
            'full_name': repo['full_name'],
            'name': repo['name'],
            'url': repo['url']
        }
        commit['_id'] = repo['full_name'] + '-' + commit['sha']
        return commit

    def scrape_commits(self, repo):
        commits_url = repo['url'] + '/commits'
        response = requests.get(commits_url, params=self.commit_params())

        while True:
            try:
                commits = response.json()
            except ValueError:
                raise ValueError(response)

            for commit in commits:
                if 'message' in commit:
                    # the repo probably has no commits
                    break
                yield self.scrape_commit(repo, commit)

            if 'next' in response.links:
                next_link = response.links['next']['url']
                response = requests.get(next_link, params=self.commit_params())
            else:
                break

    def scrape_repo(self, repo):
        print "[REPO] " + repo['name']
        for commit in self.scrape_commits(repo):
            yield commit

    def scrape(self):
        for organization in self.organizations:
            repos = self.get_repos(organization)
            for repo in repos:
                for commit in self.scrape_repo(repo):
                    yield commit
