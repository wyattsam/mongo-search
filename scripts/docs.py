#!/usr/bin/env python
"""Scrape the MongoDB manual."""

import requests
import sys
from datetime import datetime
from pymongo import MongoClient

MONGO = MongoClient('localhost:27017')
DB = MONGO['xgen']

if len(sys.argv) > 1:
    DB.authenticate(sys.argv[1], sys.argv[2])

SCRAPES = DB['scrapes']
COMBINED = DB['combined']
DOCS = DB['docs']

def save_doc_pages(source_name, id_tag, file_list_url):
    file_list = requests.get(file_list_url)
    for file_url in file_list.text.split('\n'):
        if not file_url:
            # Blank line in file.
            continue

        try:
            file_json = requests.get(file_url).json()
        except ValueError:
            print "Failed to parse json in %s" % file_url
            continue

        if 'text' not in file_json:
            print("Skipping %s" % file_url)
        else:
            print(file_url)
            doc = {
                '_id':  id_tag + file_json['current_page_name'],
                'title': file_json['title'],
                'body': file_json['text'],
                'url':  file_json['url'],
                'subsource': source_name,
            }

        DOCS.save(doc)
        doc['source'] = 'docs'
        COMBINED.save(doc)

if __name__ == '__main__':
    scrape = SCRAPES.insert({
        'source': 'docs',
        'start': datetime.now(),
        'state': 'running'
    })

    try:
        save_doc_pages(source_name='mongodb',
                       id_tag='docs-manual-', 
                       file_list_url='http://docs.mongodb.org/manual/json/.file_list')
        save_doc_pages(source_name='ecosystem',
                       id_tag='docs-ecosystem-', 
                       file_list_url='http://docs.mongodb.org/ecosystem/json/.file_list')
      # save_doc_pages(source_name='MMS',
      #                id_tag='mms-saas-', 
      #                file_list_url='http://mms.10gen.com/help/json/.file_list')
      # save_doc_pages(source_name='MMS On-Prem',
      #                id_tag='mms-hosted-', 
      #                file_list_url='http://mms.10gen.com/help-hosted/current/json/.file_list')

        SCRAPES.update({'_id': scrape},
            { '$set': { 'state': 'complete', 'end': datetime.utcnow()} })
    except Exception as error:
        SCRAPES.update({'_id': scrape},
            { '$set': { 'state': 'failed', 'error': error} })

