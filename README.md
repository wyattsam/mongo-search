DISCLAIMER
----------
Please note: all tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. We disclaim any and all warranties, either express or implied, including but not limited to any warranty of noninfringement, merchantability, and/ or fitness for a particular purpose. We do not warrant that the technology will meet your requirements, that the operation thereof will be uninterrupted or error-free, or that any errors will be corrected.
Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.

MongoDB Search
==============
A domain-specific search engine powered by MongoDB.

### Deploying
Deploying the pre-packaged site requires only a few steps.

1. Start a MongoDB instance configured to your liking on port 27017.
2. Run ```python scrape.py``` to collect data. (Warning, it takes quite a while to collect all the data and requires about 2GB of disk space.)
3. Run ```python util/indexes.py``` to build the index. (This may also take upwards of 10 minutes, depending on how much data you collected.)
4. Run ```python search.py```. The search engine is now deployed to ```localhost:5000```.

For instructions on the query language, see the cheat sheet on the home page of your deployment.

### Scheduling scrapes
It is recommended to schedule scrapes in some way to keep your data up to date. The recommended method of this is with ```cron```; hence an example ```crontab``` is included.

The file ```tasks.py``` is included to allow the scrapers to be run with [Celery](http://celeryproject.org). To start the celery workers, run:
```
$ celery -A tasks worker
$ python tasks.py
```
Executing tasks.py will queue up an initial scrape for each data source. When a source is finished, its default behavior is to immediately start again. For this reason, it's advisable to run celery in the background by using celeryd (or your favorite solution).

Scrapes that run after the initial ones are __incrememtal__, only looking for data that's updated since the previous scrape (although this behavior is not currently available in Confluence). Consider this when deciding how often to scrape.

### Building new data sources
Several common data sources, such as Stack Overflow, Github, and JIRA are available out of the box. However, defining other data sources is possible. There are a handful of steps required.

1. Build a new scraper for your source in the ```scrapers``` directory. It should inherit from ```base_scraper.BaseScraper``` and implement the ```_scrape``` (and possibly ```_setup```) methods. If your scraper requires setup, make sure to set the ```self.needs_setup``` flag to True. The purpose of the scraper is to describe the logic behind any RESTful API you may be using. Once you are done and want to use your scraper, import it inside the ```scrapers/__init__.py``` file.
2. Build a transformer for your new data source. This simply packages the raw data your scraper saved into a small, more web-friendly format. As with the scraper, define it in the ```transformers``` directory and import it in ```transformers/__init__.py```. 
3. Add a results template to ```templates/results```. If you want your template to have special styling, you should add style information to ```static/style.css```.
4. Add a configuration field to ```config/search.py```. There is a lot of information to specify here. The following is an example configuration object:
```python
 # in config/search.py
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
