# Duck Duck Mongo

### Activate environment
`source env/bin/activate'

### Setup
`pip install -r requirements.txt`

### Run locally -- Mac OS X
`brew install mongodb`
add `setParameter=textSearchEnabled=true` to /usr/local/etc/mongod.conf
`launchctl stop homebrew.mxcl.mongodb`
`launchctl start homebrew.mxcl.mongodb`
`honcho start`

### Deployment
make sure aws-test-dev.pem is in ~/.ssh or edit the fabfile.py
`fab deploy`
