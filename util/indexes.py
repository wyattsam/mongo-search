from pymongo import MongoClient

#-----------------------------------------------------------------------------
# Indexes
#-----------------------------------------------------------------------------

CONNECTION = MongoClient('/tmp/mongodb-27017.sock')

# Setup database
DB = CONNECTION['duckduckmongo']
"""
CREDENTIALS = settings.SEARCH['credentials']
USER = CREDENTIALS['user']
PASSWORD = CREDENTIALS['password']

# Login if credentials provided
if USER and PASSWORD:
    DB.authenticate(USER, PASSWORD)
"""
# Setup collections
COMBINED = DB['combined']

# Drop all the indexes before building
COMBINED.drop_indexes()

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

COMBINED.ensure_index([
    ('source', 1),
    ('subsource', 1)
    ],
    name='source_index'
)
