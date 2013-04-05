#!/usr/bin/env python
import requests
from pymongo import Connection
from time import sleep

MONGO = Connection('localhost:27017')
DB = MONGO['xgen']
COMBINED = DB['combined']
COMMITS = DB['github']
API_BASE = 'https://api.github.com/'
ORGS_URL = API_BASE + 'orgs/'
PER_PAGE = 100
CLIENT_ID = '10346e4112a4437615df'
CLIENT_SECRET = 'd8bf753eb3ad7b1aadbe91edb8507c2b05d57476'
OAUTH_PARAMS = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}
COMMIT_PARAMS = dict(OAUTH_PARAMS, per_page=PER_PAGE)

def save_repo_commits(repo):
    commits_url = repo['url'] + '/commits'
    response = requests.get(commits_url, params=COMMIT_PARAMS)

    while True:
        commits = response.json()

        for commit in commits:
            commit['repo'] = {
                'full_name': repo['full_name'],
                'name': repo['name'],
                'url': repo['url']
            }
            #print "upserting commit for " + repo['full_name'] + ":" + commit['sha']
            COMMITS.update(
                {'repo.full_name': repo['full_name'], 'sha': commit['sha']},
                commit, True
            )
            commit['source'] = 'github'
            COMBINED.update(
                {'repo.full_name': repo['full_name'], 'sha': commit['sha']},
                commit, True
            )

        if response.links.get('next'):
            next_link = response.links['next']['url']
            response = requests.get(next_link, params=COMMIT_PARAMS)
        else:
            break


def save_organizations(organizations):
    for organization in organizations:
        print "[ORG] " + organization
        repos = requests.get(ORGS_URL + organization + '/repos',
            params=OAUTH_PARAMS).json()
        for repo in repos:
            print "[REPO] " + repo['name']
            save_repo_commits(repo)

if __name__ == '__main__':
    save_organizations(['mongodb'])

