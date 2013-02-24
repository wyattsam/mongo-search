from base64 import b64encode
#from flask import Flask, request
from httplib import HTTPSConnection
from json import loads
from pymongo import Connection
from time import sleep

#app = Flask( __name__ )

#@app.route( '/api/jira_hook', methods=[ 'POST' ] )
def get( num ):

#    issueUrl = request.json[ 'issue' ][ 'self' ]
    issueUrl = 'https://jira.mongodb.org/rest/api/latest/issue/CS-' + str( num )
    print issueUrl

    jiraConn = HTTPSConnection( 'jira.mongodb.org' )
    login = b64encode( b'jiraUser:jiraPass' ).decode( 'ascii' )
    headers = { 'Authorization' : 'Basic %s' % login }
    jiraConn.request( 'GET', issueUrl, headers=headers )
    jiraResponse = jiraConn.getresponse().read()
    jiraTicketData = loads( jiraResponse )
    print jiraTicketData
    jiraTicketData[ '_id' ] = jiraTicketData[ 'key' ]

    mongo = Connection( 'mongoUrl' )
    db = mongo[ 'search' ]
    db.authenticate( 'mongoUser', 'mongoPass' )
    db.jira.save( jiraTicketData )

    return ''

if __name__ == '__main__':
    for i in range( 1, 5000 ):
        try:
            get( i )
        except:
            pass
        sleep( 2 )
