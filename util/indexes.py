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

from pymongo import MongoClient

#-----------------------------------------------------------------------------
# Indexes
#-----------------------------------------------------------------------------

CONNECTION = MongoClient('/tmp/mongodb-27017.sock')

# Setup database
DB = CONNECTION['duckduckmongo']

# Setup collections
COMBINED = DB['combined']
SEARCHES = DB['searches']
USERS = DB['users']

# Drop all the indexes before building
COMBINED.drop_indexes()

### Primary text index
COMBINED.ensure_index([
    # Stack Overflow
    ('title', 'text'),
    ('body', 'text'),

    # Stack Overflow
    ('tags', 'text'),
    ('owner.display_name', 'text'),
    ('comments.body', 'text'),
    ('answers.body', 'text'),
    ('answers.comments.body', 'text'),

    # JIRA
    ('_id', 'text'),
    ('project', 'text'),
    ('fields.summary', 'text'),
    ('fields.description', 'text'),
    ('fields.comment.comments.body', 'text'),
    ('fields.comment.comments.author.displayName', 'text'),

    # GitHub
    ('commit.sha', 'text'),
    ('commit.committer.name', 'text'),
    ('commit.committer.email', 'text'),
    ('commit.author.name', 'text'),
    ('commit.author.email', 'text'),
    ('commit.message', 'text'),

    # Profiles
    ('full_name', 'text'),
    ('crowd_id', 'text'),
    ('github', 'text'),

    # Google Groups
    ('subject', 'text'),
    ],
    name='search_index',
    weights= {
        'title': 150,
        'tags': 25,
        'fields.summary': 50,
        'fields.description': 10,
        'commit.message': 10,
        'project': 250,
        '_id' : 300,
        'full_name': 500,
        'crowd_id': 500,
        'subject': 100
    }
)

### Source filtering
COMBINED.ensure_index([
    ('source', 1),
    ('subsource', 1)
    ],
    name='source_index'
)

### Autocomplete
SEARCHES.ensure_index([
    ('query', 'text')
    ],
    name='query_text'
)
