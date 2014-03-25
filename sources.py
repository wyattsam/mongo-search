SOURCES = {
    'stack_overflow': 'Stack Overflow',
    'jira':           'JIRA',
    'google_groups':  'Google Groups',
    'github':         'GitHub',
    'chat':           '10gen Chat',
    'confluence':     'Confluence',
    'docs':           'Docs',
    'profiles':       'Profiles'
}

SUBSOURCES = {
    'stack_overflow':   None,
    'jira':             {'name': 'project', 'field': 'project'},
    'google_groups':    None,
    'github':           {'name': 'repo', 'field': 'repo.name'},
    'chat':             None,
    'docs':             {'name': 'section', 'field': 'section'},
    'confluence':       {'name': 'space', 'field': 'space'},
    'profiles':         None
}

