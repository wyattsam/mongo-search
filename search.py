from flask import Flask, request, render_template, url_for, json
from pymongo import MongoClient
from datetime import datetime
import helpers

CONNECTION = MongoClient('/tmp/mongodb-27017.sock')

# Setup database
DB = CONNECTION['xgen']
DB.authenticate('search', 'g00gl3sux')

# Setup collections
COMBINED = DB['combined']
SEARCHES = DB['searches']
PHANTOM = DB['phantom']
PAGE_SIZE = 10
COUNT_LIMIT = 1000000

SOURCES = {
    'stack_overflow': 'StackOverflow',
    'jira':           'JIRA',
    'google':         'Google Groups',
    'github':         'GitHub',
    'chat':           '10gen Chat',
    'docs':           'Docs'
}

COUNT_PROJECTION = {
    '_id': 0,
    'source': 1,
    'repo.name': 1,
    'project': 1,
    'tags': 1,
    'subsource': 1
}

RESULT_PROJECTION = {
    # Common
    'source': 1,
    'status': 1,
    'url': 1,
    'summary': 1,
    'snippet': 1,

    # GitHub
    'committer': 1,
    'html_url': 1,
    'repo': 1,
    'commit.committer': 1,
    'commit.message': 1,
    'commit.html_url': 1,
    'commit.repo.full_name': 1,

    # Jira
    'project': 1,
    'fields.summary': 1,
    'fields.description': 1,

    # Stack Overflow
    'link': 1,
    'title': 1,
    'body': 1,
    'tags': 1
}

app = Flask(__name__)

#-----------------------------------------------------------------------------
# Controllers
#-----------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/phantom", methods=["POST", "OPTIONS"])
@helpers.crossdomain(origin="*", attach_to_all=True, automatic_options=True,
    headers=["Content-length","Content-type","Connection"])
def phantom():
    topics = json.loads(request.data)
    for topic in topics:
        PHANTOM.insert(topic)

    return "wow"

@app.route("/search")
def submit():
    query = request.args.get('query', '')
    source = request.args.get('source', '')
    project = request.args.get('project', '')
    repo = request.args.get('repo', '')
    manual = request.args.get('manual', '')
    page = int(request.args.get('page', 1))
    sources = request.args.getlist('source')

    from query_parse import MongoQuery
    query_parser = MongoQuery()
    query_parser.parse(query)

    # if no sources are selected, disregard it and turn them all on.
    if len(set(sources).union(query_parser.source_filter)) == 0:
        sources = SOURCES.keys()

    for multisource in sources:
        query_parser.source_filter.add(multisource)

    if repo:
        query_parser.repo_filter.add(repo)
    if project:
        query_parser.project_filter.add(project)
    if manual:
        query_parser.manual_filter.add(manual)

    docfilter = query_parser.build_filter()
    parsed_query = query_parser.full_text_query

    search = {
        'time': datetime.now(),
        'query': query
    }

    if source:
        search['source'] = source
    if project or repo or manual:
        search['subsource'] = project or repo or manual
    SEARCHES.insert(search)

    #run the counts separately using covered query
    if not parsed_query:
        parsed_query = ' '

    covered_results = run_count_query(parsed_query)
    counts = helpers.get_counts(covered_results)
    counts['filter_total'] = len(run_count_query(parsed_query, docfilter))

    page_limit = page * PAGE_SIZE

    results = run_query(parsed_query, page, docfilter, page_limit)
    pagination = helpers.Pagination(page, PAGE_SIZE, counts['filter_total'])

    return render_template('results.html', results=results,
        counts=counts,
        sources_searched=set(sources).union(query_parser.source_filter),
        sub_source=(repo or project or manual),
        query=parsed_query,
        pagination=pagination)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#-----------------------------------------------------------------------------
# Helpers
#-----------------------------------------------------------------------------

def run_count_query(query, docfilter=None):
    return DB.command('text', 'combined',
        search=query,
        filter=docfilter,
        project=COUNT_PROJECTION,
        limit=COUNT_LIMIT
    )['results']

def run_query(query, page, docfilter, limit):
    results = DB.command('text', 'combined',
        search=query,
        filter=docfilter,
        limit=limit,
        project=RESULT_PROJECTION
    )['results']

    massaged = helpers.massage_results(results, query)

    start = (page - 1) * PAGE_SIZE
    end = page * PAGE_SIZE
    return sorted(massaged, key=lambda k: -k['score'])[start:end]

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

