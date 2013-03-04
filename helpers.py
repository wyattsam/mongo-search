import json
import re

JIRA_URL = "https://jira.mongodb.org/browse/"

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
        'score': post['score'],
        'url': post['link'],
        'summary': post['title'],
        'snippet': re.sub('<[^<]+?>', '', post['body']),
        'source': 'so'
    }
    return massaged

def massage_jira(issue):
    massaged = {
        'score': issue['score'],
        'url': JIRA_URL + issue['key'],
        'summary': issue['fields']['summary'],
        'snippet': issue['fields']['description'],
        'source': 'jira'
    }
    return massaged