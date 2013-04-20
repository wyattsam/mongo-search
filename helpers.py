from collections import Counter
import json
import re
from math import ceil

JIRA_URL = "https://jira.mongodb.org/browse/"

def get_counts_by_source(raw_results):
    source_counts = Counter((doc['obj']['source'] for doc in raw_results))
    return source_counts 

def massage_results(raw_results, query):
    massaged = []

    for result in raw_results:
        current = result['obj']
        current['score'] = result['score']
        source = current['source']

        if source == 'so':
            massaged.append(massage_stack_overflow(current))
        elif source == 'jira':
            massaged.append(massage_jira(current))

    return massaged

def massage_stack_overflow(post):
    massaged = {
        'id': post['_id'],
        'score': post['score'],
        'url': post['link'],
        'summary': post['title'],
        'snippet': re.sub('<[^<]+?>', '', post['body']),
        'source': 'so'
    }
    return massaged

def massage_jira(issue):
    massaged = {
        'id': issue['_id'],
        'score': issue['score'],
        'url': JIRA_URL + issue['key'],
        'summary': issue['fields']['summary'],
        'snippet': issue['fields']['description'],
        'source': 'jira'
    }
    return massaged

class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def lower_bound(self):
        return (self.page - 1) * self.per_page + 1

    @property
    def upper_bound(self):
        return min((self.page-1) * self.per_page + self.per_page, self.total_count)

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self):
        for num in xrange(1, self.pages + 1):
           yield num

