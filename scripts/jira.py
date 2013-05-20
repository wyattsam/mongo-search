#!/usr/bin/env python
import sys
import requests
from pymongo import Connection
from time import sleep

MONGO = Connection('localhost:27017')
DB = MONGO['xgen']
COMBINED = DB['combined']
ISSUES = DB['jira']
API_BASE = 'https://jira.mongodb.org/rest/api/2/'
SEARCH_URL = API_BASE + 'search/'
PROJECT_URL = API_BASE + 'project/'
PAGE_SIZE = 100

def jira_get(url, params={}, login=False):
    auth = credentials if login else {}
    return requests.get(url, params=params, auth=auth, verify=False).json()

def save_issue(issue, project):
    #print "upserting jira issue " + issue['key']
    key = issue['key']
    issue['_id'] = key
    issue['project'] = project
    issue['fields']['status'] = issue['fields']['status']['name']
    ISSUES.save(issue)
    issue['source'] = 'jira'
    COMBINED.save(issue)

def save_issues(project):
    jql = 'PROJECT={project} order by KEY asc'.format(project=project)
    params = {
        'jql': jql,
        'startAt': 0,
        'maxResults': PAGE_SIZE,
        'fields': 'key,summary,description,comment,status'
    }

    while True:
        result = jira_get(SEARCH_URL, params=params)
        if not 'issues' in result:
            break

        issues = result['issues']
        if issues:
            for issue in issues:
                save_issue(issue, project)
        else:
            break

        params['startAt'] += len(issues)
        sleep(1)

if __name__ == '__main__':
    global credentials
    login = False

    # user provided login credentials
    if len(sys.argv) == 3:
        jira_user, jira_pass = sys.argv[1:3]
        credentials = (jira_user, jira_pass)
        login = True

    projects = jira_get(PROJECT_URL, login=login)

    project_keys = [project['key'] for project in projects]
    print "getting jira issues for the following projects: " + str(project_keys)
    for project_key in project_keys:
        print "[PROJECT] " + project_key
        save_issues(project_key)
