#!/usr/bin/env python
import sys
import requests
from datetime import datetime
from pymongo import Connection
from time import sleep

MONGO = Connection('localhost:27017')
DB = MONGO['xgen']

if len(sys.argv) == 5:
    DB.authenticate(sys.argv[3], sys.argv[4])

SCRAPES = DB['scrapes']
COMBINED = DB['combined']
ISSUES = DB['jira']
API_BASE = 'https://jira.mongodb.org/rest/api/2/'
SEARCH_URL = API_BASE + 'search/'
PROJECT_URL = API_BASE + 'project/'
PAGE_SIZE = 100
SKIP_PROJECTS = ['FREE']

def jira_get(url, params={}, credentials=None):
    auth = credentials if credentials else {}
    response = requests.get(url, params=params, auth=auth, verify=False)
    return response.json()

def save_issue(issue, project):
    #print "upserting jira issue " + issue['key']
    key = issue['key']
    issue['_id'] = key
    issue['project'] = project
    issue['fields']['status'] = issue['fields']['status']['name']
    ISSUES.save(issue)
    issue['source'] = 'jira'
    COMBINED.save(issue)

def save_issues(project, credentials=None):
    jql = 'PROJECT={project} order by KEY asc'.format(project=project)
    params = {
        'jql': jql,
        'startAt': 0,
        'maxResults': PAGE_SIZE,
        'fields': 'key,summary,description,comment,status'
    }

    while True:
        result = jira_get(SEARCH_URL, params=params, credentials=credentials)
        if 'issues' not in result:
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
    scrape = SCRAPES.insert({
        'source': 'jira',
        'start': datetime.utcnow(),
        'state': 'running'
    })

    # user provided login credentials
    credentials = None
    if len(sys.argv) >= 3:
        jira_user, jira_pass = sys.argv[1:3]
        credentials = (jira_user, jira_pass)

    try:
        projects = jira_get(PROJECT_URL, credentials=credentials)
        project_keys = [project['key'] for project in projects]

        for project_key in project_keys:
            if project_key in SKIP_PROJECTS:
                print "[SKIP] " + project_key
                continue
            else:
                print "[PROJECT] " + project_key
                save_issues(project_key, credentials)

        SCRAPES.update({'_id': scrape},
            { '$set': { 'state': 'complete', 'end': datetime.now()} })

    except Exception as error:
        SCRAPES.update({'_id': scrape},
            { '$set': { 'state': 'failed', 'error': error} })
