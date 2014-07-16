# Copyright 2014 MongoDB Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import scrapers as scrapers
import transformers as transformers
import indexing.hooks as hooks
import logging

CONFIG = {
    'stackoverflow': {
        'fullname': 'Stack Overflow',
        'scraper': scrapers.StackOverflowScraper,
        'transformer': transformers.StackOverflowTransformer,
        'subsources': None,
        'projector': {
            'link': 1,
            '_id': 1,
            'title': 1,
            'body': 1,
            'tags': 1,
            'answer_count': 1,
            'is_answered': 1,
            'score': 1
        },
        'view': 'results/stackoverflow_result.html',
        'advanced': [
            {
                'name': 'Total views',
                'field': 'view_count',
                'type': 'text'
            },
            {
                'name': 'Is answered',
                'field': 'is_answered',
                'type': 'radio',
                'options': [('Yes', 'true'), ('No', 'false')]
            }
        ],
        'tags': []
    },
    'jira': {
        'fullname': 'JIRA',
        'scraper': scrapers.JiraScraper,
        'transformer': transformers.JiraTransformer,
        'subsources': {
            'name': 'project',
            'field': 'project'
        },
        'projector': {
            '_id': 1,
            'fields': 1,
            'subsource': 1,
            'id': 1
        },
        'view': 'results/jira_result.html',
        'advanced': [
            {
                'name': 'Status',
                'field': 'fields.status',
                'type': 'dropdown',
                'options': ['Open', 'Resolved', 'Closed']
            },
            {
                'name': 'Total comments',
                'field': 'fields.comment.total',
                'type': 'text'
            }
        ],
        'auth': {
            'user': '',
            'password': ''
        },
        'skip': ['FREE'],
    },
    'github': {
        'fullname': 'GitHub',
        'scraper': scrapers.GithubScraper,
        'transformer': transformers.GithubTransformer,
        'subsources': {
            'name': 'repo',
            'field': 'repo.name'
        },
        'projector': {
            'html_url': 1,
            'repo': 1,
            'commit': 1,
            '_id': 1,
            'org': 1,
            'subsource': 1
        },
        'view': 'results/github_result.html',
        'advanced': [
            {
                'name': 'Repository',
                'field': 'repo.name',
                'type': 'text'
            },
            {
                'name': 'Organization',
                'field': 'org',
                'type': 'text'
            }
        ],
        'auth': {
            'client_id': '',
            'client_secret': ''
        },
        'orgs': ['mongodb']
    },
    'googlegroups': {
        'fullname': 'Google Groups',
        'scraper': scrapers.IMAPScraper,
        'transformer': transformers.IMAPTransformer,
        'subsources': None,
        'projector': {
            '_id': 1,
            'subject': 1,
            'from': 1,
            'sender': 1,
            'body': 1,
            'group': 1
        },
        'view': 'results/imap_result.html',
        'auth': {
            'user': '',
            'password': ''
        },
        'labels': ['freesupport']
    },
    'confluence': {
        'fullname': 'Confluence',
        'scraper': scrapers.ConfluenceScraper,
        'transformer': transformers.ConfluenceTransformer,
        'subsources': {
            'name': 'space',
            'field': 'space'
        },
        'projector': { 
            '_id': 1,
            'body': 1,
            'space': 1,
            'url': 1,
            'title': 1,
            'subsource': 1
        },
        'view': 'results/confluence_result.html',
        'auth': {
            'user': '',
            'password': ''
        },
        'spaces': []
    },
    '_loglevel': logging.DEBUG
}

SEARCH = {'credentials': {'user': None, 'password': None}}

HOOKS = {
    'github': hooks.GithubHook,
    'jira': hooks.JiraHook
}
