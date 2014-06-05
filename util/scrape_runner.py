import inspect
import scrapers

from pymongo import MongoClient

class ScrapeRunner(object):
    def __init__(self):
        self.client = MongoClient('localhost:27017')
        self.db = self.client['duckduckmongo']
        self.combined = self.db.combined

        self.scrapers = [m[1] for m in inspect.getmembers(scrapers, inspect.isclass)]

    def save(self, document, srcname):
        document['source'] = srcname
        self.combined.save(document)

    def run(self):
        for s in self.scrapers:
            for d in s.documents():
                try:
                    self.save(r, s.name)
                except:
                    # TODO log something?
                    continue
