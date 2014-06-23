from socket import gethostbyname
from celery import Celery
from pymongo import MongoClient

class BaseHook(object):
    def __init__(self, hostname):
        self.needs_auth = False
        self.ip = gethostbyname(hostname)
        self.celery = Celery('base_hook')
        client = MongoClient('localhost:27017')
        db = client['duckduckmongo']
        self.combined = db['combined']

    def receive(self, msg):
        self.handle.delay(msg)
