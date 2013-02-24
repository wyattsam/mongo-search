from flask import Flask, request, render_template
from pymongo import MongoClient
import pdb

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
    return render_template('results.html', results=results)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#-----------------------------------------------------------------------------
# Helpers
#-----------------------------------------------------------------------------

def run_query(query):
    # print "QUERY: " + query
    connection = MongoClient('localhost', 27017)
    db = connection.DDM
    q = db.command('text', 'test', search=query, limit=10)
    results = q['results']
    # print "RESULTS: " + str(results)
    return results

#-----------------------------------------------------------------------------
# Launch
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    app.debug = True
    app.run()