#!/usr/bin/env python
from pyquery import PyQuery as pq
import requests
import re
import pymongo
from time import sleep

MONGO_HOST = 'localhost'
MONGO_DATABASE = 'xgen'
MONGO_COLLECTION = 'google_groups'

#pq(t('div.msg div.mb')[0]).text()
thread_link_pattern = re.compile('/group/mongodb-user/browse_thread/thread/(\w+)')
thread_ids = set()

def get_topic_links(start_page=0, max_page=-1):
    index = 0
    page = start_page
    while True:
        if max_page > 0 and page >= max_page:
            break
        index_page = requests.get('https://groups.google.com/group/mongodb-user/topics', params={'hl':'en', 'start':page, 'sa':'N'})
        if index_page.status_code != 200:
            raise
        t = pq(index_page.content)
        tid_size = len(thread_ids)
        links_on_page = set()
        for a_tag in t.find('a'):
            x2 = pq(a_tag)
            match_url = thread_link_pattern.match(x2.attr('href'))
            if match_url and match_url not in thread_ids:
                thread_ids.add(match_url.group(1))
                links_on_page.add(match_url.group(1))

        if links_on_page:
            for link in links_on_page:
                yield link
        else:
            break
        page += 10

def get_thread_messages(thread_id):
    params = {'hl':'en', 'noredirect':'true', 'pl1':'1'}
    page = requests.get('http://groups.google.com/group/mongodb-user/browse_thread/thread/%s' % thread_id,params=params)
    if page.status_code != 200:
        raise
    t = pq(page.content)
    message_divs = t.find('div#inbdy')
    messages = []
    for div in message_divs:
        message_parts = pq(div).children()
        message = ""
        for message_p in message_parts:
            content = pq(message_p).text()
            content.replace(u'\xa0', u' ')
            if content.strip().startswith('- Show quoted text -') \
                or content.strip().startswith('- Hide quoted text -'):
                break
            else:
                if content.startswith('> '):
                    content = content[2:]
                message += content
        messages.append(message)
    return messages

def scrape():
  conn = pymongo.MongoClient(MONGO_HOST)
  db = conn[MONGO_DATABASE]
  coll = db[MONGO_COLLECTION]
  for t in get_topic_links():
      print "fetching thread:", t
      messages = get_thread_messages(t)
      print "got", len(messages), "messages."
      doc = {'_id':t, 'messages':messages}
      coll.save(doc)

if __name__ == '__main__':
    scrape()

