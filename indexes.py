#-----------------------------------------------------------------------------
# Indexes
#-----------------------------------------------------------------------------

COMBINED.ensure_index([
    # Stack Overflow
    ('title', 'text'),
    ('body', 'text'),
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

    # GitHub
    ('commit.message', 'text'),

    # Appended field for covered count query
    ('source', 1)
],
    name='search_index',
    weights= {
        'title': 150,
        'tags': 25,
        'fields.summary': 150,
        'fields.description': 5,
        'commit.message': 5,
        'project': 250,
        '_id' : 300
    }
)

GITHUB.ensure_index('tickets')
