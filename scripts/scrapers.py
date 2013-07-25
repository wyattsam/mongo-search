import requests
import sys
import traceback
from datetime import datetime
from pymongo import MongoClient


class ScrapeRunner(object):

    def login(self):
        user = self.credentials['user']
        password = self.credentials['password']
        if user and password:
            self.db.authenticate(user, password)

    def __init__(self, database, credentials=None):
        # mongo
        self.client = MongoClient('localhost:27017')
        self.db = self.client[database]
        self.combined = self.db.combined
        self.scrapes = self.db.scrapes
        self.credentials = credentials
        self.scrape_id = None
        if credentials:
            self.login()

    def _start_scrape(self, name):
        start = {
            'source': name,
            'start': datetime.utcnow(),
            'state': 'running'
        }
        self.scrape_id = self.scrapes.insert(start)

    def _scrape_error(self, error):
        scrape = {'_id': self.scrape_id}
        exc_type, exc_value, exc_trace = sys.exc_info()
        update = {'$set': {
            'state': 'error',
            'error': str(error),
            'trace': traceback.format_exception(exc_type, exc_value, exc_trace)
        }}
        self.scrapes.update(scrape, update)
        self.scrape_id = None

    def _end_scrape(self):
        scrape = {'_id': self.scrape_id}
        update = {'$set': {
            'state': 'complete',
            'end': datetime.utcnow()
        }}
        self.scrapes.update(scrape, update)

    def _save(self, name, collection, document):
        collection.save(document)
        document['source'] = name
        self.combined.save(document)

    def run(self, scraper):
        name = scraper.NAME
        collection = self.db[name]
        self._start_scrape(name)

        try:
            for document in scraper.scrape():
                self._save(name, collection, document)
        except Exception as error:
            self._scrape_error(error)
            return

        self._end_scrape()


class Scraper(object):

    def scrape(self):
        raise NotImplementedError


class JSONScraper(Scraper):

    def get_json(self, url, params={}, auth=None):
        if auth:
            user = auth['user']
            password = auth['password']
            if user and password:
                auth = tuple([user, password])
            else:
                auth = None

        response = requests.get(url, params=params, auth=auth, verify=False)
        return response.json()
