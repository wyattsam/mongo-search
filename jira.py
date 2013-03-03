#!/usr/bin/env python
import sys
import requests
from pymongo import Connection
from time import sleep

MONGO = Connection('localhost:27017')
DB = MONGO['xgen']
ISSUES = DB['jira']
API_BASE = 'https://jira.mongodb.org/rest/api/latest/'
ISSUE_URL = API_BASE + 'issue/'
SEARCH_URL = API_BASE + 'search/'
PROJECT_URL = API_BASE + 'project/'

def jira_get(url, params={}, login=True):
    auth = credentials if login else {}
    return requests.get(url, params=params, auth=auth, verify=False).json()


def save_issue(issue_key):
    print "getting " + issue_key
    issue = jira_get(ISSUE_URL + issue_key)
    issue['_id'] = issue['key']
    ISSUES.save(issue)

def save_issues(project):
    jql = 'PROJECT={project} order by KEY asc'.format(project=project)
    params = {
        'jql': jql,
        'startAt': 0,
        'maxResults': 100,
        'fields': 'KEY'
    }

    while True:
        result = jira_get(SEARCH_URL, params=params)
        issues = result['issues']

        if issues:
            for issue in issues:
                save_issue(issue['key'])
                sleep(0.25)
        else:
            break

        params['startAt'] += len(issues)

if __name__ == '__main__':
    global credentials

    if len(sys.argv) < 3:
        print "usage: jira.py jira_username jira_password"
        sys.exit(0)

    jira_user, jira_pass = sys.argv[1:3]
    credentials = (jira_user, jira_pass)
    projects = jira_get(PROJECT_URL, login=False)
    project_keys = [project['key'] for project in projects]
    print project_keys
    for project_key in project_keys:
        save_issues(project_key)