import re
import md5
from flask import request
from collections import Counter
from math import ceil

CORP_URL = 'https://corp.10gen.com/'
JIRA_URL = "https://jira.mongodb.org/browse/"


def corp_url():
    if request.referrer and 'mongodb' in request.referrer:
        return CORP_URL.replace('10gen', 'mongodb')
    else:
        return CORP_URL


def get_counts(raw_results):
    counts = {
        'total': 0,
        'source': Counter(),
        'repo': Counter(),
        'project': Counter(),
        'section': Counter(),
        'space': Counter()
    }

    for doc in raw_results:
        source = doc['_id']['source']

        if 'subsource' in doc['_id']:
            subsource = doc['_id']['subsource']
        else:
            subsource = None

        count = doc['count']

        counts['total'] += count
        counts['source'][source] += count

        source_subsource_map = {
            'github': 'repo',
            'jira': 'project',
            'docs': 'section',
            'confluence': 'space'
        }

        if subsource:
            subsource_name = source_subsource_map[source]
            counts[subsource_name][subsource] += count

    return counts


def massage_results(raw_results):
    massaged = []

    for result in raw_results:
        source = result['source']

        source_massage_map = {
            'stack_overflow': massage_stack_overflow,
            'jira': massage_jira,
            'github': massage_github,
            'docs': massage_docs,
            'profiles': massage_profile,
            'google_groups': massage_google,
            'confluence': massage_confluence
        }

        massager = source_massage_map[source]
        massaged.append(massager(result))

    return massaged


def massage_google(post):
    massaged = {
        'score': post['score'],
        'source': 'google',
        'subject': post['subject'],
        'body': post['body'],
        'group': post['group'],
        'from': post['from'],
        'sender': post['sender']
    }
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
        "committer": commit['commit']['committer']['name'],
        "committer_avatar": committer.get('avatar_url', ''),
        "date_committed": commit['commit']['committer']['date'],
        "commit_msg": commit_msg_header,
        "commit_msg_body": commit_msg_body,
        "url": commit['html_url'],
        "repo_name": commit['repo']['full_name']
    }
    return massaged


def massage_profile(profile):
    massaged = {
        'id': profile['crowd_id'],
        'first_name': profile['first_name'],
        'last_name': profile['last_name'],
        'full_name': profile['full_name'],
        'url': corp_url() + 'employees/' + profile['crowd_id'],
        'score': profile['score'],
        'source': 'profiles',
        'team': profile['team']['name'],
        'office': profile['office'],
        'email': profile['primary_email'],
        'phone': profile['primary_phone'],
        'github': profile['github'],
        'title': profile['title'],
        'md5': md5.new(profile['primary_email'].strip().lower()).hexdigest(),
        'snippet': profile['bio']
    }
    return massaged


def massage_docs(doc):
    return doc


def massage_stack_overflow(post):
    massaged = {
        'id': post['_id'],
        'score': post['score'],
        'url': post['link'],
        'summary': post['title'],
        'snippet': re.sub('<[^<]+?>', '', post['body']),
        'source': 'stack_overflow'
    }
    return massaged


def massage_jira(issue):
    massaged = {
        'id': issue['_id'],
        'fields': issue['fields'],
        'status': issue.get('fields', {}).get('status', None),
        'score': issue['score'],
        'url': JIRA_URL + issue['_id'],
        'summary': issue['fields'].get('summary', ''),
        'snippet': issue['fields'].get('description', ''),
        'source': 'jira'
    }
    return massaged


def massage_confluence(page):
    massaged = {
        'id': page['_id'],
        'title': page['title'],
        'body': page['body'],
        'url': page['url'],
        'space': page['space'],
        'source': 'confluence',
        'score': page['score']
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
