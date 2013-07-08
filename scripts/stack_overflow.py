#!/usr/bin/env python
import sys
import requests
from datetime import datetime
from pymongo import Connection
from time import sleep

MONGO = Connection('localhost:27017')
DB = MONGO['xgen']

if len(sys.argv) > 1:
    DB.authenticate(sys.argv[1], sys.argv[2])

SCRAPES = DB['scrapes']
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
            STACK_OVERFLOW.save(item)
            item['source'] = 'so'
            COMBINED.save(item)

        if not result.get('has_more'): break

        # don't remove this -- back off if you're told to backoff
        if result.has_key('backoff'):
            sleep(result['backoff'])

        params['page'] += 1

if __name__ == '__main__':
    scrape = SCRAPES.insert({
        'source': 'so',
        'start': datetime.utcnow(),
        'state': 'running'
    })

    try:
        save_questions('mongodb')
        SCRAPES.update({'_id': scrape},
            { '$set': { 'state': 'complete', 'end': datetime.now()} })

    except Exception as error:
        SCRAPES.update({'_id': scrape},
            { '$set': { 'state': 'failed', 'error': error} })
