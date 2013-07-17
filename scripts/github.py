import requests
from scrapers import JSONScraper


class GitHubScraper(JSONScraper):
    NAME = 'github'
    API_BASE = 'https://api.github.com/'
    ORGS_URL = API_BASE + 'orgs/'
    PER_PAGE = 100
    CLIENT_ID = '10346e4112a4437615df'
    CLIENT_SECRET = 'd8bf753eb3ad7b1aadbe91edb8507c2b05d57476'
    OAUTH_PARAMS = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}
    COMMIT_PARAMS = dict(OAUTH_PARAMS, per_page=PER_PAGE)

    def get_repos(self, organization):
        url = self.ORGS_URL + organization + '/repos'
        repos = self.get_json(url, self.OAUTH_PARAMS)
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
        response = requests.get(commits_url, params=self.COMMIT_PARAMS)

        while True:
            commits = response.json()
            for commit in commits:
                if 'message' in commit:
                    # the repo probably has no commits
                    break
                yield self.scrape_commit(repo, commit)

            if 'next' in response.links:
                next_link = response.links['next']['url']
                response = requests.get(next_link, params=self.COMMIT_PARAMS)
            else:
                break

    def scrape_repo(self, repo):
        print "[REPO] " + repo['name']
        for commit in self.scrape_commits(repo):
            yield commit

    def scrape(self):
        repos = self.get_repos('mongodb')
        for repo in repos:
            for commit in self.scrape_repo(repo):
                yield commit
