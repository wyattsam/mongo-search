from collections import Counter
import json
import re
from math import ceil

JIRA_URL = "https://jira.mongodb.org/browse/"

def get_counts(raw_results):
    counts = {
        'total': 0,
        'source': Counter(),
        'repo': Counter(),
        'project': Counter(),
        'tag': Counter()
    }

    for doc in raw_results:
        obj = doc['obj']

        counts['total'] += 1
        counts['source'][obj['source']] += 1

        if obj['source'] == 'github':
            counts['repo'][obj['repo']['name']] += 1

        if obj['source'] == 'jira':
            counts['project'][obj['project']] += 1

    return counts

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
        elif source == 'github':
            massaged.append(massage_github(current))

    return massaged

def massage_github(commit):
    committer = commit['committer'] or {}
    commit_msg_header = commit['commit']['message']
    commit_msg_body = None
    newline_pos = commit_msg_header.find('\n')
    if newline_pos >= 0:
        commit_msg_body = commit_msg_header[newline_pos:].strip()
        commit_msg_header = commit_msg_header[0:newline_pos].strip()

    massaged = {
        'id': commit['_id'],
        'score': commit['score'],
        'source': 'github',
        "committer" : commit['commit']['committer']['name'],
        "committer_avatar" : committer.get('avatar_url', ''),
        "date_committed" : commit['commit']['committer']['date'],
        "commit_msg" : commit_msg_header,
        "commit_msg_body" : commit_msg_body,
        "url" : commit['html_url'],
        "repo_name" : commit['repo']['full_name']
    }
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
        'fields' : issue['fields'],
        'status': issue.get('fields',{}).get('status',None),
        'score': issue['score'],
        'url': JIRA_URL + issue['_id'],
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
        for num in xrange(self.page, min(self.pages + 1, self.page + 10)):
           yield num

