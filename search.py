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

#-----------------------------------------------------------------------------
# App Config
#-----------------------------------------------------------------------------
app = Flask(__name__)

#-----------------------------------------------------------------------------
# Controllers
#-----------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template('index.html')


@app.route("/search")
def submit():
    args = request.args
    query, source_filter, page = parse_args(args)

    #run the counts separately using covered query
    counts = covered_count(query, source_filter)

    page_limit = page * PAGE_SIZE

    results = run_query(query, page, source_filter, page_limit)
    pagination = helpers.Pagination(page, PAGE_SIZE, counts['filter_total'])

    return render_template('results.html', results=results,
        counts=counts,
        sources_searched=request.args.getlist('source'),
        sub_source=hack_sub_source(source_filter) or 'MongoDB Universe',
        query=query,
        pagination=pagination)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#-----------------------------------------------------------------------------
# Helpers
#-----------------------------------------------------------------------------

def hack_sub_source(source_filter):
    subsource = (source_filter.get('project') or
        source_filter.get('repo.name') or
        source_filter.get('subsource'))
    if subsource:
        subsource = subsource['$in'][0]
    return subsource


def covered_count(query, source_filter):
    covered_results = run_count_query(query)
    counts = helpers.get_counts(covered_results)
    counts['filter_total'] = len(run_count_query(query, source_filter))

    return counts

def log_search(query, source, subsource):
    search = {
        'time': datetime.utcnow(),
        'query': parsed_query
    }

    if source:
        search['source'] = source
    if project or repo or manual:
        search['subsource'] = project or repo or manual

    SEARCHES.insert(search)

def parse_args(args):
    query = args.get('query', '')
    page = int(args.get('page', 1))

    from query_parse import MongoQuery
    query_parser = MongoQuery()
    query_parser.parse(query)

    parse_source(query_parser, args)
    parse_subsource(query_parser, args)

    parsed_query = query_parser.full_text_query
    source_filter = query_parser.build_filter()

    return parsed_query, source_filter, page

def parse_source(parser, args):
    sources = args.getlist('source')

    # if no sources are selected, disregard it and turn them all on.
    if len(set(sources).union(parser.source_filter)) == 0:
        sources = SOURCES.keys()

    # add all the sources to the parser
    for multisource in sources:
        parser.source_filter.add(multisource)

def parse_subsource(parser, args):
    manual = args.get('manual', '')
    project = args.get('project', '')
    repo = args.get('repo', '')

    if repo:
        parser.repo_filter.add(repo)
    if project:
        parser.project_filter.add(project)
    if manual:
        parser.manual_filter.add(manual)

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

#-----------------------------------------------------------------------------
# Logging
#-----------------------------------------------------------------------------

ADMINS = ['tyler@10gen.com']

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    from logging.handlers import RotatingFileHandler
    mail_handler = SMTPHandler('127.0.0.1',
                               'search@10gen.com',
                               ADMINS, '10gen Search Error')
    file_handler = RotatingFileHandler('./log/flask.log')
    mail_handler.setLevel(logging.ERROR)
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(mail_handler)

