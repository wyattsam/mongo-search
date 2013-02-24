from StringIO import StringIO
import time
import urllib
import json
import gzip
import pymongo
from BeautifulSoup import BeautifulSoup

username = 'search'
password = '10gen'

#conn = pymongo.Connection('mongodb://50.19.0.111:8000')
conn = pymongo.Connection()
db = conn['search']
#db.authenticate(username, password)

def fetch_and_insert(page_num, coll):
    handle = urllib.urlopen('https://api.stackexchange.com/2.1/questions?page=%d&pagesize=100&order=desc&sort=activity&tagged=mongodb&site=stackoverflow&filter=!bULULVX1DHh2eg' % (page_num,))
    unzipped = gzip.GzipFile(fileobj=StringIO(handle.read()))
    data = json.load(unzipped)
    print 'Quota remaining: %s' % (data['quota_remaining'],)

    for item in data['items']:
        soup = BeautifulSoup(item['body'])
        item['body'] = soup.text
        coll.insert(item)

    time.sleep(data.get('backoff', 1.0)) #Hope I have that json field right. 
    return data

#fetch_and_insert(80, db['stackoverflow'])
