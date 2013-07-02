#!/usr/bin/env python
"""Scrape the MongoDB manual."""

import requests
import sys
from pymongo import MongoClient

MONGO = MongoClient('localhost:27017')
DB = MONGO['xgen']

if len(sys.argv) > 1:
    DB.authenticate(sys.argv[1], sys.argv[2])

COMBINED = DB['combined']
DOCS = DB['docs']


def save_doc_pages():
    file_list_url = 'http://docs.mongodb.org/manual/json/.file_list'

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
                '_id':  'docs-manual-' + file_json['current_page_name'],
                'title': file_json['title'],
                'body': file_json['text'],
                'url':  file_json['url'],
                'subsource': 'mongodb',
            }

        DOCS.save(doc)
        doc['source'] = 'docs'
        COMBINED.save(doc)

if __name__ == '__main__':
    save_doc_pages()

