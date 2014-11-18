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

import logging

import scrapers as scrapers
import transformers as transformers
import indexing.hooks as hooks
from config.private import CONFIG as PRIVATE_CONFIG

## Deep dict merge.
def merge(a, b):
    if not isinstance(a, dict) or not isinstance(b, dict):
        raise Exception("`merge` must pass a dict for both parameters")

    out = dict(a)

    for key in b.keys():
        if key in a.keys() and isinstance(a[key], dict) and isinstance(b[key], dict):
            out[key] = merge(a[key], b[key])
        else:
            out[key] = b[key]

    return out

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
                'name': 'Score',
                'field': 'score',
                'type': 'text'
            },
            {
                'name': 'Is answered',
                'field': 'is_answered',
                'type': 'radio',
                'options': [('Yes', 'true'), ('No', 'false')]
            }
        ],
        'tags': ['mongodb', 'replication', 'sharding', 'nosql']
    },
    'docs-core': {
        'fullname': 'MongoDB Documentation',
        'scraper': scrapers.DocsScraper,
        'transformer': transformers.DocsTransformer,
        'subsources': {
            'name': 'section',
            'field': 'section'
        },
        'projector': {
            '_id': 1,
            'title': 1,
            'text': 1,
            'subsource': 1,
            'section': 1,
            'current_page_name': 1,
            'meta': 1,
            'url': 1,
            'metatags': 1
        },
        'view': 'results/docs_result.html',
        'advanced': [
            {
                'name': 'Section',
                'field': 'section',
                'type': 'text'
            }
        ],
        'siteurl': 'http://docs.mongodb.org/',
        'kinds': ['manual', 'ecosystem'] ## Defines the feeds to fetch from for the scraper
    },
    'docs-mms-classic': {
        'fullname': 'MMS Classic Documentation',
        'scraper': scrapers.DocsScraper,
        'transformer': transformers.DocsTransformer,
        'subsources': {
            'name': 'classic-section',
            'field': 'classic-section'
        },
        'projector': {
            '_id': 1,
            'title': 1,
            'text': 1,
            'subsource': 1,
            'section': 1,
            'current_page_name': 1,
            'meta': 1,
            'url': 1,
            'metatags': 1
        },
        'view': 'results/docs_result.html',
        'advanced': [
            {
                'name': 'Section',
                'field': 'section',
                'type': 'text'
            }
        ],
        'siteurl': 'https://mms.mongodb.com/',
        'kinds': ['help-classic', 'help-hosted/current']
    },
    'docs-mms-onprem': {
        'fullname': 'MMS On-Prem Documentation',
        'scraper': scrapers.DocsScraper,
        'transformer': transformers.DocsTransformer,
        'subsources': {
            'name': 'onprem-section',
            'field': 'onprem-section'
        },
        'projector': {
            '_id': 1,
            'title': 1,
            'text': 1,
            'subsource': 1,
            'section': 1,
            'current_page_name': 1,
            'meta': 1,
            'url': 1,
            'metatags': 1
        },
        'view': 'results/docs_result.html',
        'advanced': [
            {
                'name': 'Section',
                'field': 'section',
                'type': 'text'
            }
        ],
        'siteurl': 'https://mms.mongodb.com/',
        'kinds': ['help-hosted/current']
    },
    'docs-mms-cloud': {
        'fullname': 'MMS Cloud Documentation',
        'scraper': scrapers.DocsScraper,
        'transformer': transformers.DocsTransformer,
        'subsources': None,
        'projector': {
            '_id': 1,
            'title': 1,
            'text': 1,
            'subsource': 1,
            'section': 1,
            'current_page_name': 1,
            'meta': 1,
            'url': 1,
            'metatags': 1
        },
        'view': 'results/docs_result.html',
        'advanced': [
            {
                'name': 'Section',
                'field': 'section',
                'type': 'text'
            }
        ],
        'siteurl': 'https://docs.mms.mongodb.com/',
        'kinds': ['']
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
            'user': 'xgen-internal-search',
            'password': 'xxx'
        },
        'skip': ['FREE'],
    },
    'github': {
        'fullname': 'GitHub',
        'scraper': scrapers.GithubScraper,
        'transformer': transformers.GithubTransformer,
        'subsources': {
            'name': 'repo',
            'field': 'repo'
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
            'client_id': 'xxx',
            'client_secret': 'xxx'
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
            'user': 'info@10gen.com',
            'password': 'xxx'
        },
        'labels': ['freesupport']
    },
    'profiles': {
        'fullname': 'Profiles',
        'scraper': scrapers.ProfilesScraper,
        'transformer': transformers.ProfilesTransformer,
        'subsources': None,
        'projector': {
            '_id': 1,
            'crowd_id': 1,
            'first_name': 1,
            'last_name': 1,
            'full_name': 1,
            'team': 1,
            'office': 1,
            'primary_email': 1,
            'primary_phone': 1,
            'github': 1,
            'title': 1,
            'bio': 1
        },
        'view': 'results/profiles_result.html',
        'advanced': [
            {
                'name': 'Office',
                'field': 'office',
                'type': 'text'
            },
            {
                'name': 'Team',
                'field': 'team.name',
                'type': 'text'
            }
        ],
        'auth': {
            'user': 'employee_api',
            'password': 'xxx'
        },
        'digest': True
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
            'user': 'xgen-internal-search',
            'password': 'xxx'
        },
        'spaces': [
            '10GEN',
            'cs',
            'sales',
            'OPSIT',
            'KB',
            'mcs',
            'mrkt',
            'HGTC',
            'MMS',
            'KERNEL'
        ]
    },
    '_loglevel': logging.DEBUG
}

CONFIG = merge(CONFIG, PRIVATE_CONFIG)

SEARCH = {'credentials': {'user': None, 'password': None}}

HOOKS = {
    'github': hooks.GithubHook,
    'jira': hooks.JiraHook
}

