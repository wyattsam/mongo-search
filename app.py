from flask import Flask, request, render_template, url_for, redirect
from pymongo import MongoClient
from datetime import datetime
from query.parser import BasicQuery, BasicQueryVisitor
from flask_debugtoolbar import DebugToolbarExtension
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile
import util.helpers as helpers
import config.duckduckmongo as settings
import json

CONNECTION = MongoClient('/tmp/mongodb-27017.sock')

# Setup database
DB = CONNECTION['duckduckmongo']

CREDENTIALS = settings.SEARCH['credentials']
USER = CREDENTIALS['user']
PASSWORD = CREDENTIALS['password']

# Login if credentials provided
if USER and PASSWORD:
    DB.authenticate(USER, PASSWORD)
else:
    print "Not authenticating, no username or password provided"

# Setup collections
COMBINED = DB['combined']
SEARCHES = DB['searches']
SCRAPES = DB['scrapes']

SOURCES = [k for k in settings.CONFIG.keys() if k[0] != '_']
SUBSOURCES = dict([(n, settings.CONFIG[n]['subsources']) for n in SOURCES])

BASIC_OPTS = [  'query' 
              , 'source'
              , 'subsource'
              , 'page'
              , 'advanced'
              ]
BASIC_OPTS.extend([k for k in SUBSOURCES.keys() if SUBSOURCES[k]])

# App Settings
PAGE_SIZE = 10

"""
RESULT_PROJECTION = {
    # Common
    'text_score': {'$meta': 'textScore'},
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
    'fields.status': 1,
    'fields.comment.total': 1,

    # Stack Overflow
    'link': 1,
    'title': 1,
    'body': 1,
    'tags': 1,
    'answer_count': 1,
    'is_answered': 1,
    'score': 1,

    # Profiles
    'crowd_id': 1,
    'first_name': 1,
    'last_name': 1,
    'full_name': 1,
    'github': 1,
    'primary_phone': 1,
    'title': 1,
    'team.name': 1,
    'office': 1,
    'uri': 1,
    'primary_email': 1,
    'bio': 1,

    # Google Groups
    'subject': 1,
    'from': 1,
    'sender': 1,
    'group': 1,

    # Confluence
    'space': 1,

    # Docs
    'section': 1,
}
"""

RESULT_PROJECTION = {
    'text_score': {'$meta': 'textScore'},
    'source': 1,
    'subsource': 1
}

for s in SOURCES:
    RESULT_PROJECTION.update(settings.CONFIG[s]['projector'])
#-----------------------------------------------------------------------------
# App Config
#-----------------------------------------------------------------------------
app = Flask(__name__)

#-----------------------------------------------------------------------------
# Controllers
#-----------------------------------------------------------------------------


@app.route("/", methods=["GET", "POST"])
@line_profile
def index():
    ac = ""
    if request.method == 'POST':
        ac = autocomplete_list(str(request.data))

    version = DB.command({'buildInfo': 1})['version']

    if len(ac) > 0:
        ac = map(str, ac)
        ac = map(json.dumps, ac)

    return render_template('index.html', version=version, ac=ac)


@app.route("/search", methods=["GET", "POST"])
@line_profile
def submit():
    ac = ""
    if request.method == 'POST':
        ac = autocomplete_list(str(request.data))
    args = request.args
    log_search(args)
    if len(ac) > 0:
        ac = map(str, ac)
        ac = map(json.dumps, ac)

    mq, page = parse_args(args)

    if not mq.query:
        return redirect('/')

    #run the counts separately using covered query
    visitor = BasicQueryVisitor(mq)
    query_json = visitor.visit_all()
    if 'advanced' in args and args['advanced']:
        query_json = advanced_options(query_json, mq.args)
    counts = covered_count(query_json, mq.args)

    page_limit = page * PAGE_SIZE

    results = run_query(query_json, mq.args, page, page_limit)
    pagination = helpers.Pagination(page, PAGE_SIZE, counts['filter_total'])

    return render_template(
        'results.html',
        results=results,
        counts=counts,
        source=mq.args.get('source', ''),
        sub_source=mq.args.get('subsource', ''),
        query=mq,
        ac=ac,
        pagination=pagination
    )


@app.route("/status")
@line_profile
def status():
    scrapes = get_scrapes()
    return render_template('status.html', scrapes=scrapes)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#-----------------------------------------------------------------------------
# Helpers
#-----------------------------------------------------------------------------

@line_profile
def get_scrapes():
    scrapes = {}

    for source in SOURCES:
        result = SCRAPES.find_one(
            {'source': source},
            sort=[('start', -1)]
        )
        if result:
            last_success = SCRAPES.find_one(
                {'source': source, 'state': 'complete'},
                sort=[('start', -1)])
            if last_success:
                result['last_success'] = last_success['end']
            scrapes[source] = result

    return scrapes


@line_profile
def parse_args(args):
    page = int(args.get('page', 1))
    return BasicQuery(args, SUBSOURCES), page


@line_profile
def covered_count(query_doc, args):
    unfiltered_results = run_count_query(query_doc)
    filtered_results = run_filtered_count_query(query_doc)
    counts = helpers.get_counts(unfiltered_results, SUBSOURCES)
    if filtered_results < counts['total']:
        counts['filtered'] = filtered_results

    if 'subsource' in query_doc:
        subsource_name = SUBSOURCES[query_doc['source']]['name']
        counts['filter_total'] = counts[subsource_name][query_doc['subsource']]
    elif 'source' in query_doc:
        counts['filter_total'] = counts['source'][query_doc['source']]
    else:
        counts['filter_total'] = counts['total']

    return counts

@line_profile
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

    SEARCHES.insert(search, w=0)

@line_profile
def run_count_query(query_doc):
    # remove all filters for the overall count query
    q = dict([('$text', query_doc['$text'])])
    return COMBINED.aggregate([
        {'$match': q},
        {'$group':
            {
                '_id': {'source': '$source', 'subsource': '$subsource'},
                'count': {'$sum': 1}
            }
         },
    ])['result']

@line_profile
def run_filtered_count_query(query_doc):
    return COMBINED.find(query_doc).count()

@line_profile
def run_query(query_doc, args, page, limit):
    # must use $orderby for sort until pymongo is updated
    sort_doc = {'text_score': {'$meta': 'textScore'}}

    results = COMBINED.find(
        {
            '$query': query_doc,
            '$orderby': sort_doc
        },
        limit=limit,
        fields=RESULT_PROJECTION
    )

    transformed = []
    for result in results:
        source = result['source']
        if settings.CONFIG[source]['transformer']:
            transformer = settings.CONFIG[source]['transformer']()
            transformed.append(transformer.transform(result))

    start = (page - 1) * PAGE_SIZE
    end = page * PAGE_SIZE
    return transformed[start:end]

@line_profile
def advanced_options(doc, args):
    aargs = []
    # TODO should use a generic visitor here
    # also this is horrible
    for k in args:
        if k not in BASIC_OPTS:
            if args[k]:
                aargs.append(parse_advanced(k, args[k]))
    for a in aargs:
        doc.update(a)
    return doc

@line_profile
def parse_advanced(k, arg):
    digits = '0123456789'
    bools = {
        'true': True,
        'false': False
    }
    ineqs = {
        '+': '$gte',
        '-': '$lte'
    }
    if arg[0] in digits:
        try:
            if len(arg) > 1:
                lastchar = arg[-1:]
                v = int(arg[:-1])
                if lastchar in ineqs.keys():
                    return {k: {ineqs[lastchar]: v}}
            return {k: int(arg)}
        except:
            pass
    elif arg in bools.keys():
        return {k: bools[arg]}
    else:
        return {k: arg}

@line_profile
def url_for_other_page(page):
    args = request.args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)

def autocomplete_list(prefix):
    v = SEARCHES.aggregate([{
        '$match': {
            'query': { '$regex': prefix }
        }
    },
    {
        '$group': {
            '_id': { 'query': '$query' },
            'count': { '$sum': 1 }
        }
    },
    {
        '$sort': {
            'count': -1
        }
    }
    ])['result'][:15]
    ret = [doc['_id']['query'] for doc in v]
    print ret
    return ret


app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['SOURCES'] = SOURCES
app.jinja_env.globals['SUBSOURCES'] = SUBSOURCES
app.jinja_env.globals['CONFIG'] = settings.CONFIG


#-----------------------------------------------------------------------------
# Launch
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    app.debug = True
    app.config['SECRET_KEY'] = 'supersekretkey'

    # Specify the debug panels you want
    app.config['DEBUG_TB_PANELS'] = [
        'flask_debugtoolbar.panels.versions.VersionDebugPanel',
        'flask_debugtoolbar.panels.timer.TimerDebugPanel',
        'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
        'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'flask_debugtoolbar.panels.template.TemplateDebugPanel',
        'flask_debugtoolbar.panels.logger.LoggingPanel',
        'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        # Add the line profiling
        'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel'
        # Add the MongoDB profiling
        #'flask_debugtoolbar_mongo.panel.MongoDebugPanel'
    ]

    toolbar = DebugToolbarExtension(app)

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
