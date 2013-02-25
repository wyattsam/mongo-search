#!/usr/bin/env python
import requests
import json
import sys
import pymongo

import settings
COOKIES = settings.partychapp['cookies']

HANDLER = 'http://chat.10gen.com/logentriesjson/'
MAX_MESSAGES = 100

MONGO_HOST = 'localhost'
MONGO_DATABASE = 'xgen'
MONGO_COLLECTION = 'partychapp'

def fetch(channel):
  req_data = {
    'channelName': channel,
    'limit': MAX_MESSAGES,
    'offset': 0,
  }
  resp = requests.post(url=HANDLER, data=req_data, cookies=COOKIES)
  if resp.status_code != 200:
    print "server returned code %d" % resp.status_code
    return []
  resp_data = json.loads(resp.text)
  if 'error' in resp_data:
    print "server returned error: %s" % resp.text
    return []
  return resp_data['entries']

def save(conn, messages, channel):
  coll = conn[MONGO_DATABASE][MONGO_COLLECTION]
  for m in messages:
    m['channel'] = channel
    coll.insert(m)

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print "usage: %s name_of_channel" % sys.argv[0]
    sys.exit(1)
  channel = sys.argv[1]
  conn = pymongo.MongoClient(MONGO_HOST)
  messages = fetch(channel)
  save(conn, messages, channel)
  print "saved %d messages" % len(messages)
