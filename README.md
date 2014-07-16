MongoDB Search
==============
A domain-specific search engine powered by MongoDB.

### Deploying
Deploying the pre-packaged site requires only a few steps.

1. Start a MongoDB instance configured to your liking on port 27017.
2. Run ```python scrape.py``` to collect data. (Warning, it takes quite a while to collect all the data and requires about 2GB of disk space.)
3. Run ```python util/indexes.py``` to build the index. (This may also take upwards of 10 minutes, depending on how much data you collected.)
4. Run ```python app.py```. The search engine is now deployed to ```localhost:5000```.

For instructions on the query language, see the cheat sheet on the home page of your deployment.

### Using Celery to scrape
The file ```tasks.py``` is included to allow the scrapers to be run with [Celery](http://celeryproject.org). To start the celery workers, run:
```
$ celery -A tasks worker
$ python tasks.py
```
Executing tasks.py will queue up an initial scrape for each data source. When a source is finished, its default behavior is to immediately start again. For this reason, it's advisable to run celery in the background by using celeryd (or your favorite solution).

### Building new data sources
Several common data sources, such as Stack Overflow, Github, and JIRA are available out of the box. However, defining other data sources is possible. There are a handful of steps required.

1. Build a new scraper for your source in the ```scrapers``` directory. It should inherit from ```base_scraper.BaseScraper``` and implement the ```_scrape``` (and possibly ```_setup```) methods. If your scraper requires setup, make sure to set the ```self.needs_setup``` flag to True. The purpose of the scraper is to describe the logic behind any RESTful API you may be using. Once you are done and want to use your scraper, don't import it inside the ```scrapers/__init__.py``` file.
2. Build a transformer for your new data source. This simply packages the raw data your scraper saved into a small, more web-friendly format. As with the scraper, define it in the ```transformers``` directory and import it in ```transformers/__init__.py```. 
3. Add a results template to ```templates/results```. If you want your template to have special styling, you should add style information to ```static/style.css```.
4. Add a configuration field to ```config/duckduckmongo.py```. There is a lot of information to specify here. The following is an example configuration object:
```python
 # in config/duckduckmongo.py
CONFIG = {
    ...
    'my_new_source': {
        'fullname': 'My New Source', # the display name
        'scraper': scrapers.MyNewScraper, # how to scrape for this source
        'transformer': transformers.MyNewTransformer, # how to transform
        'subsources': { # if you have subsources, define their description here. otherwise, this field is None
            'name': 'section',
            'field': 'some_json_field'
        },
        'projector': {
            # all the fields you want saved by the scraper. just include the field name with a value of 1.
        },
        'view': 'results/my_new_source_result.html', # the display template
        'advanced': [ # the list of advanced search options
            {
                'name': 'An Advanced Field',
                'field': 'some_field',
                'type': 'text'
            }
        ],
        'auth': { # auth information. if your source does not need any, leave it out.
            'user': 'username',
            'password': 'password'
        },
        # if you want any other information included, add it here
    },
    ...
}
```
Now you can run your scraper by running ```python scrape.py my_new_source```. Once it's all done, you're ready to search!
