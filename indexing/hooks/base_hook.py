from socket import gethostbyname
from pymongo import MongoClient

class BaseHook(object):
    def __init__(self, hostname):
        self.needs_auth = False
        client = MongoClient('localhost:27017')
        db = client['duckduckmongo']
        self.combined = db['combined']

    def receive(self, msg):
        # TODO should call celery
        # apparently blocked on celery being useless with classes
        self.handle(msg)
