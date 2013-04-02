#!/usr/bin/env python
import sys
import requests
#import settings
from pymongo import Connection
from time import sleep

MONGO = Connection('localhost:27017')
DB = MONGO['xgen']
COMBINED = DB['combined']
STACK_OVERFLOW = DB['stack_overflow']
API_BASE = 'https://api.stackexchange.com/2.1/'
SEARCH_URL = API_BASE + 'search'
PAGE_SIZE = 100

def save_questions(tag):
    print "[TAG] " + tag
    params = {
        'site': 'stackoverflow',
        'tagged': tag,
        'filter': '!*1Klotvkqr2dciMbX*Qdafx4aenCPiyZAdUE1x(1w',
        'sort': 'creation',
        'order': 'asc',
        'page': 1,
        'pagesize': PAGE_SIZE,
        #'key': settings.stackapp['key']
    }

    while True:
        result = requests.get(SEARCH_URL, params=params).json()
        items = result.get('items', [])

        for item in items:
            key = 'SO-' + str(item['question_id'])
            item['_id'] = key
            #print "upserting stack overflow question " + key
            STACK_OVERFLOW.update({'_id': key}, item, True)
            item['source'] = 'so'
            COMBINED.update({'_id': key}, item, True)

        if not result.get('has_more'): break

        # don't remove this -- back off if you're told to backoff
        if result.has_key('backoff'):
            sleep(result['backoff'])

        params['page'] += 1

if __name__ == '__main__':
    save_questions('mongodb')
