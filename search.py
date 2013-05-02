from flask import Flask, request, render_template, url_for
from pymongo import MongoClient

import helpers

CONNECTION = MongoClient('localhost', 27017)
ADMIN = CONNECTION['admin']
ADMIN.command('setParameter', textSearchEnabled=True)
DB = CONNECTION['xgen']
COMBINED = DB['combined']
GITHUB = DB['github']
PAGE_SIZE = 10
SEARCH_LIMIT = 100000

SOURCES = {
    'so':     'StackOverflow',
    'jira':   'JIRA',
    'google': 'Google Groups',
    'github': 'GitHub',
    'chat':   '10gen Chat'
}

RESULT_PROJECTION = {
    # Common
    'source': 1,
    'status': 1,
    'url': 1,
    'summary': 1,
    'snippet': 1,

    # GitHub
    'commit.committer.name': 1,
    'commit.committer.avatar_url': 1,
    'commit.committer.date': 1,
    'commit.message': 1,
    'commit.html_url': 1,
    'commit.repo.full_name': 1,

    # Jira
    'fields': 1,
    'key': 1,

    # Stack Overflow
    'link': 1,
    'title': 1,
    'body': 1
}

app = Flask(__name__)

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
    ('commit.message', 'text')
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

#-----------------------------------------------------------------------------
# Controllers
#-----------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/search")
def submit():
    query = request.args.get('query', '')
    page = int(request.args.get('page', 1))
    sources = request.args.getlist('source')

    from query_parse import MongoQuery
    query_parser = MongoQuery()
    query_parser.parse(query)

    # if no sources are selected, disregard it and turn them all on.
    if len(set(sources).union(query_parser.source_filter)) == 0:
        sources = SOURCES.keys()

    for source in sources:
        query_parser.source_filter.add(source)

    docfilter = query_parser.build_filter()

    results, source_counts = run_query(query_parser.full_text_query, page, docfilter)
    total_count = sum(source_counts.values())
    pagination = helpers.Pagination(page, PAGE_SIZE, total_count)

    return render_template('results.html', results=results,
        source_counts=source_counts,
        sources_searched=set(sources).union(query_parser.source_filter),
        query=query_parser.full_text_query,
        pagination=pagination)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#-----------------------------------------------------------------------------
# Helpers
#-----------------------------------------------------------------------------

def run_query(query, page, docfilter):
    results = DB.command('text', 'combined',
        search=query,
        filter=docfilter,
        limit=SEARCH_LIMIT,
        project=RESULT_PROJECTION
    )['results']

    source_counts = helpers.get_counts_by_source(results)
    massaged = helpers.massage_results(results, query)

    start = (page - 1) * PAGE_SIZE
    end = page * PAGE_SIZE
    return sorted(massaged, key=lambda k: -k['score'])[start:end], source_counts

def url_for_other_page(page):
    args = request.args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['SOURCES'] = SOURCES

#-----------------------------------------------------------------------------
# Launch
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    app.debug = True
    app.run()

