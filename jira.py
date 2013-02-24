#!/usr/bin/env python
import sys
import requests
from pymongo import Connection
from time import sleep

MONGO = Connection( 'mongodb://xgen:xgen@localhost:27017/xgen' )
DB = MONGO['xgen']
ISSUE_BASE = 'https://jira.mongodb.org/rest/api/latest/issue/'

def get( project, num, username, password ):
    issue_url = ISSUE_BASE + project + '-' + str( num )
    print issue_url
    response = requests.get(issue_url, auth=(username, password), verify=False)
    jira_ticket_data = response.json()
    jira_ticket_data[ '_id' ] = jira_ticket_data[ 'key' ]
    DB.jira.save( jira_ticket_data )

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage: jira.py jira_username jira_password"
        sys.exit(0)

    jira_user, jira_pass = sys.argv[1:3]

    for i in range( 1, 5000 ):
        get( 'CS', i, jira_user, jira_pass )
        sleep( 2 )
