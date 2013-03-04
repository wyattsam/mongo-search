from flask import Flask, request, render_template
from pymongo import MongoClient

import helpers

CONNECTION = MongoClient('localhost', 27017)
ADMIN = CONNECTION['admin']
ADMIN.command('setParameter', textSearchEnabled=True)
DB = CONNECTION['xgen']
COMBINED = DB['combined']

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
    ('project', 'text'),
    ('fields.summary', 'text'),
    ('fields.description', 'text'),
    ('fields.summary', 'text'),
    ('fields.comment.comments.body', 'text')
],
    name='search_index',
    weights= {
        'title': 50,
        'tags': 25,
        'summary': 50,
        'description': 25
    }
)

#-----------------------------------------------------------------------------
# Controllers
#-----------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/submit", methods=['POST','GET'])
def submit():
    query = request.args['query']
    results = run_query(query)
    return render_template('results.html', results=results, query=query)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#-----------------------------------------------------------------------------
# Helpers
#-----------------------------------------------------------------------------

def run_query(query):
    results = DB.command('text', 'combined', search=query, limit=10)['results']
    massaged = helpers.massage_results(results, query)

    return sorted(massaged, key=lambda k: k['score'])

#-----------------------------------------------------------------------------
# Launch
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    app.debug = True
    app.run()