from flask import Flask, request, render_template
from pymongo import MongoClient

import helpers

app = Flask(__name__)

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
    connection = MongoClient('localhost', 27017)
    db = connection.xgen
    
    q = db.command('text', 'jira', search=query, limit=10)
    jira_results = helpers.clean_jira_results(q['results'], query)

    q = db.command('text', 'partychapp', search=query, limit=10)
    chat_results = helpers.clean_chat_results(q['results'], query)

    return sorted(jira_results + chat_results, key=lambda k: k['score'])

#-----------------------------------------------------------------------------
# Launch
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    app.debug = True
    app.run()