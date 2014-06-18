import re
import md5
from flask import request
from collections import Counter
from math import ceil
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile

CORP_URL = 'https://corp.10gen.com/'
JIRA_URL = "https://jira.mongodb.org/browse/"

@line_profile
def corp_url():
    if request.referrer and 'mongodb' in request.referrer:
        return CORP_URL.replace('10gen', 'mongodb')
    else:
        return CORP_URL


@line_profile
def get_counts(raw_results, ss):
    ss_names = [ss[s]['name'] for s in ss.keys() if ss[s]]
    ss_fields = [ss[s]['field'] for s in ss.keys() if ss[s]]
    counts = {
        'total': 0,
        'source': Counter()
    }
    for s in ss_names:
        counts[s] = Counter()

    for doc in raw_results:
        source = doc['_id']['source']
        subsource = None
        if 'subsource' in doc['_id']:
            subsource = doc['_id']['subsource']

        count = doc['count']
        counts['total'] += count
        counts['source'][source] += count

        ss_map = dict([(k,ss[k]['name']) for k in ss.keys() if ss[k]])

        if subsource:
            subsource_name = ss_map[source]
            counts[subsource_name][subsource] += count

    return counts

@line_profile
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
        return min(
            (self.page - 1) * self.per_page + self.per_page, self.total_count
        )

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
        for num in xrange(self.page, min(self.pages + 1, self.page + 10)):
            yield num
