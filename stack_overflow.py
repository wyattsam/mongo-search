#!/usr/bin/env python
import requests
from pymongo import Connection
from time import sleep

MONGO = Connection('localhost:27017')
DB = MONGO['xgen']
STACK_OVERFLOW = DB['stack_overflow']
API_BASE = 'https://api.stackexchange.com/2.1/'
SEARCH_URL = API_BASE + 'search'

def save_questions(tag):
    params = {
        'site': 'stackoverflow',
        'tagged': tag,
        'filter': '!5-2mK)UuZ8I8445X3g0zP75EnxSr_MZe.(FaBo',
        'sort': 'creation',
        'order': 'asc',
        'page': 1,
        'pagesize': 100
    }

    while True:
        result = requests.get(SEARCH_URL, params=params).json()
        items = result['items']

        for item in items:
            item['_id'] = 'SO-' + str(item['question_id'])
            STACK_OVERFLOW.save(item)
        
        if not result['has_more']: break

        if result.has_key('backoff'):
            sleep(result['backoff'])

        params['page'] += 1

if __name__ == '__main__':
    save_questions('mongodb')