from flask import Flask, request, render_template, url_for, redirect
from pymongo import MongoClient
from datetime import datetime
import helpers
import settings

CONNECTION = MongoClient('/tmp/mongodb-27017.sock')

# Setup database
DB = CONNECTION['xgen']

CREDENTIALS = settings.SEARCH['credentials']
USER = CREDENTIALS['user']
PASSWORD = CREDENTIALS['password']

# Login if credentials provided
if USER and PASSWORD:
    DB.authenticate(USER, PASSWORD)

# Setup collections
COMBINED = DB['combined']
SEARCHES = DB['searches']
PHANTOM = DB['phantom']
PAGE_SIZE = 10
COUNT_LIMIT = 1000000

SOURCES = {
    'stack_overflow': 'Stack Overflow',
    'jira':           'JIRA',
    'google':         'Google Groups',
    'github':         'GitHub',
    'chat':           '10gen Chat',
    'docs':           'Docs'
}

SUBSOURCES = {
    'stack_overflow': None,
    'jira': {'name': 'project', 'field': 'project'},
    'google': None,
    'github': {'name': 'repo', 'field': 'repo.name'},
    'chat': None,
    'docs': {'name': 'manual', 'field': 'manual'}
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
    log_search(args)

    mq, page = parse_args(args)
    print mq.filter

    if not mq.query:
        return redirect('/')

    #run the counts separately using covered query
    counts = covered_count(mq.query, mq.filter)

    page_limit = page * PAGE_SIZE

    results = run_query(mq.query, page, mq.filter, page_limit)
    pagination = helpers.Pagination(page, PAGE_SIZE, counts['filter_total'])

    return render_template('results.html', results=results,
        counts=counts,
        source=mq.source,
        sub_source=mq.sub_source,
        query=mq.query,
        pagination=pagination)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#-----------------------------------------------------------------------------
# Helpers
#-----------------------------------------------------------------------------

def parse_args(args):
    page = int(args.get('page', 1))
    from query_parse import MongoQuery
    return MongoQuery(args), page


def covered_count(query, source_filter):
    covered_results = run_count_query(query)
    counts = helpers.get_counts(covered_results)
    counts['filter_total'] = len(run_count_query(query, source_filter))

    return counts

def log_search(args):
    search = {
        'time': datetime.utcnow(),
        'query': args.get('query', None),
        'page': int(args.get('page', 1))
    }

    source = args.get('source')

    if source:
        search['source'] = source
        subsource = SUBSOURCES[source]

        if subsource and args.get(subsource['name']):
            search['subsource'] = args[subsource['name']]

    SEARCHES.insert(search)

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
app.jinja_env.globals['SUBSOURCES'] = SUBSOURCES


#-----------------------------------------------------------------------------
# Launch
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    app.debug = True

    if not app.debug:
        ADMINS = ['tyler@10gen.com']

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

    app.run()
