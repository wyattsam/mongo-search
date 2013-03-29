# Duck Duck Mongo

### Activate environment
 - `source env/bin/activate`

### Setup
 - `pip install -r requirements.txt`

### Scrapers
 - Scrape JIRA (Unauthenticated) `./scripts/jira.py`
 - Scrape Stack Overflow (Unauthenticated) `./scripts/stack_overflow.py`

### Setup MongoDB -- Mac OS X
 - run `brew install mongodb`
 - add `setParameter=textSearchEnabled=true` to /usr/local/etc/mongod.conf`
 - run `launchctl stop homebrew.mxcl.mongodb`
 - run `launchctl start homebrew.mxcl.mongodb`

### Run locally
 - `honcho start`

### Deployment
 - make sure aws-test-dev.pem is in ~/.ssh or edit the fabfile.py
 - `fab deploy`
